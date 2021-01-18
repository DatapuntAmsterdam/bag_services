"""
Typeahead bag, brk

Search    bag, brk
"""
from __future__ import annotations

import json
import logging
import re
from collections import OrderedDict
from collections import defaultdict

from rest_framework.exceptions import PermissionDenied
from typing import AbstractSet, Callable, List
from urllib.parse import quote, urlparse

from django.conf import settings
from django.utils.encoding import force_text

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import Search
from rest_framework import viewsets, metadata
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.compat import coreapi, coreschema

from bag import authorization_levels

from datasets.bag import queries as bag_qs  # noqa
from datasets.brk import queries as brk_qs  # noqa
from datasets.generic import rest
from search.query_analyzer import QueryAnalyzer


log = logging.getLogger(__name__)

CallableQueryFunction = Callable[[QueryAnalyzer], Search]

# Mapping of subtypes with detail views
_details = {
    'ligplaats': 'ligplaats-detail',
    'standplaats': 'standplaats-detail',
    'verblijfsobject': 'verblijfsobject-detail',
    'openbare_ruimte': 'openbareruimte-detail',
    'nummeraanduiding': 'nummeraanduiding-detail',
    'pand': 'pand-detail',
    'kadastraal_subject': 'kadastraalsubject-detail',
    'kadastraal_object': 'kadastraalobject-detail',
    'bouwblok': 'bouwblok-detail',

    'buurt': 'buurt-detail',
    'unesco': 'unesco-detail',
    'buurtcombinatie': 'buurtcombinatie-detail',
    'gebiedsgerichtwerken': 'gebiedsgerichtwerken-detail',
    'stadsdeel': 'stadsdeel-detail',

    # OPR
    'gebied': 'openbareruimte-detail',
    'overig terrein': 'openbareruimte-detail',

    'grootstedelijk': 'grootstedelijkgebied-detail',
    'woonplaats': 'woonplaats-detail',
}

# autocomplete_group_sizes
_autocomplete_group_sizes = {
    'Straatnamen': 8,
    'Adressen': 8,
    'Openbare ruimtes': 5,
    'Gebieden': 5,
    'Kadastrale objecten': 8,
    'Kadastrale subjecten': 5,
    'Bouwblokken': 5,
    'Panden': 5,
}

_autocomplete_group_order = [
    'Straatnamen',
    'Adressen',
    'Openbare ruimtes',
    'Gebieden',
    'Kadastrale objecten',
    'Kadastrale subjecten',
    'Bouwblokken',
    'Panden',
]

_subtype_mapping = {
    'weg': 'Straatnamen',
    'kunstwerk': 'Openbare ruimtes',
    'water': 'Openbare ruimtes',
    'terrein': 'Openbare ruimtes',
    'administratief gebied': 'Openbare ruimtes',
    'spoorbaan': 'Openbare ruimtes',
    'landschappelijk gebied': 'Openbare ruimtes',
    'nummeraanduiding': 'Adressen',
    'pand': 'Panden',
    'openbare_ruimte': 'Adressen',
    'verblijfsobject': 'Adressen',
    'ligplaats': 'Adressen',
    'standplaats': 'Adressen',
    'kadastraal_object': 'Kadastrale objecten',
    'kadastraal_subject': 'Kadastrale subjecten',
    'gemeente': 'Gebieden',
    'woonplaats': 'Gebieden',
    'unesco': 'Gebieden',
    'grootstedelijk': 'Gebieden',
    'stadsdeel': 'Gebieden',
    'gebiedsgerichtwerken': 'Gebieden',
    'buurtcombinatie': 'Gebieden',
    'overig terrein': 'Gebieden',
    'overig gebouwd object': 'Gebieden',
    'buurt': 'Gebieden',
    'bouwblok': 'Bouwblokken',
}


_add_subtype_display = {
    'kunstwerk',
    'water',
    'terrein',
    'administratief gebied',
    'spoorbaan',
    'landschappelijk gebied',
}


# A collection of regex and the query they generate
# IMPORTANT : if items are added to specialized_query_selectors it can have the negative side effect
# that default_queries are no longer selected.  Only add a new query selectors here if it does
# not clash with the queries in default queries
specialized_query_selectors = [
    {
        'labels': {'bag'},
        'testfunction': 'is_postcode_prefix',
        'query': bag_qs.postcode_query,
    },
    {
        'labels': {'bag'},
        'testfunction': 'is_bouwblok_prefix',
        'query': bag_qs.bouwblok_query,
    },
    {
        'labels': {'bag', 'nummeraanduiding'},
        'testfunction': 'is_postcode_huisnummer_prefix',
        'query': bag_qs.postcode_huisnummer_query,
    },
    {
        'labels': {'brk'},
        'testfunction': 'is_kadastraal_object_prefix',
        'query': brk_qs.kadastraal_object_query,
    },
    {
        'labels': {'nummeraanduiding'},
        'testfunction': 'is_straatnaam_huisnummer_prefix',
        'query': bag_qs.straatnaam_huisnummer_query,
    },
    {
        'labels': {'gebieden'},
        'testfunction': None,
        # 'query': bag_qs.weg_query,
        'query': bag_qs.gebied_query,
    },
    {
        'labels': {'nummeraanduiding'},
        'testfunction': 'is_landelijk_id_prefix',
        'query': bag_qs.landelijk_id_nummeraanduiding_query,
    },
    {
        'labels': {'gebieden'},
        'testfunction': 'is_landelijk_id_prefix',
        'query': bag_qs.landelijk_id_openbare_ruimte_query,
    },
    {
        'labels': {'pand'},
        'testfunction': 'is_landelijk_id_prefix',
        'query': bag_qs.landelijk_id_pand_query,
    },
]

default_queries = {
    'bag': [bag_qs.openbare_ruimte_query],
    'gebieden': [bag_qs.gebied_query],
    'pand': [bag_qs.pandnaam_query]
}


def get_specialized_query_selectors(q_select: AbstractSet[str]) -> List[dict]:
    """
    Filter the list of 'specialized_query_selectors' with the selected labels.
    """
    if not q_select:
        return list(specialized_query_selectors)

    new_selection = [a for a in specialized_query_selectors if a['labels'] & q_select]
    if not new_selection:
        raise ValueError('q_select %s not in %s', q_select, specialized_query_selectors)

    return new_selection


def find_specialized_queries(
    q_select: AbstractSet[str],
    analyzer: QueryAnalyzer,
    features: int
) -> List[CallableQueryFunction]:
    """
    Find specialized queries for a search term.
    For example, if the input looks like a postcode,
    use a special query for that.
    """
    query_selectors = get_specialized_query_selectors(q_select)
    queries = []

    # query_selectors contains the selected choices from 'specialized_query_selectors'
    for option in query_selectors:
        test_name = option.get('testfunction')
        if not test_name or not analyzer.matches_test(option['testfunction']):
            continue


        log.debug(
            'Matched %s for query <%s>',
            option['testfunction'], analyzer.query)
        query = option['query']
        queries.append(query)

    return queries


def find_default_queries(q_select, features:int = 0) -> List[Search]:
    """
    return the default queries.
    filter by selected queries if set
    """
    queries = []

    # return all defaults
    if not q_select:
        for v in default_queries.values():
            queries += v
        return queries

    # return filtered default queries
    for category in q_select:
        query = default_queries.get(category, [])
        queries += query

    return queries


def select_queries(
        query_string: str,
        analyzer: QueryAnalyzer,
        q_select: AbstractSet[str] = None,
        features: int = 0) -> List[Search]:
    """
    Looks at the query string being filled and tries
    to make conclusions about what is actually being searched.
    This is useful to reduce the number of queries and reduce the result size

    Returns a list of queries that should be used
    """

    # Too little information to search on
    if len(query_string) < 2:
        return []

    # Filter on selected services, and return those queries.
    queries = find_specialized_queries(q_select, analyzer, features)

    # Checking for a case in which no matches are found.
    # In which case, defaulting to address/openbare ruimte
    if not queries:
        log.debug("No specialized queries for '%s', using defaults", query_string)
        queries = find_default_queries(q_select, features)

    return [q(analyzer, features) for q in queries]


def _get_doc_attr(hit, attribute, default):

    if hasattr(hit, attribute):
        value = getattr(hit, attribute)
        if value:
            return value

    return default


def _get_url(request, hit):
    """
    Given an elk hit determine the uri for each hit
    """
    doc_type = _get_doc_attr(hit, 'type',  default=hit.meta.doc_type)
    detail_type = _get_doc_attr(hit, 'subtype', doc_type)

    # fallback for undefined detailview for subtype:
    if detail_type not in _details:
        detail_type = doc_type

    #  if fallback also undefined:
    if detail_type not in _details:
        raise ValueError('Cannot create self url %s %s', doc_type, hit.subtype)

    if detail_type in ('ligplaats', 'standplaats', 'verblijfsobject'):
        pk = _get_doc_attr(hit, 'adresseerbaar_object_id', default=None)
        if pk is None:  # The link to adresseerbaar_object_id is missing, this should not happen but it does
            detail_type = 'nummeraanduiding'
            pk = _get_doc_attr(hit, 'landelijk_id', default=None)
    else:
        pk = _get_doc_attr(hit, 'landelijk_id', default=None)
    if pk is None:
        pk = _get_doc_attr(hit, 'subtype_id', default=hit.meta.id)

    return rest.get_links(
        view_name=_details[detail_type],
        kwargs={'pk': pk}, request=request)


class QueryMetadata(metadata.SimpleMetadata):
    def determine_metadata(self, request, view):
        result = super().determine_metadata(request, view)
        result['parameters'] = {
            'q': {
                'type': 'string',
                'description': 'The query to search for',
                'required': False,
            },
        }
        return result


# =============================================
# Search view sets
# =============================================
class QFilter(object):
    """
    For openapi documentation purposes
    return the q field
    """
    search_title = 'search title'
    search_description = 'search description'

    subtype_title = 'search subtype'
    subtype_description = 'search only in subtype or negation with not_'

    def get_schema_fields(self, _view):
        """
        return Q parameter documentation
        """
        return [
            coreapi.Field(
                name='q',
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_text(self.search_title),
                    description=force_text(self.search_description)
                )
            ),
            coreapi.Field(
                name='subtype',
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_text(self.subtype_title),
                    description=force_text(self.subtype_description)
                )
            )
        ]


class TypeaheadViewSet(viewsets.ViewSet):
    """
    Given a query parameter `q`, this function returns a
    subset of all objects
    that (partially) match the specified query.

    *NOTE*

    We assume spelling errors and therefore it is possible
    to have unexpected results

    We use many datasets by trying to guess about the input
    - adresses, public spaces, bouwblok

    """
    metadata_class = QueryMetadata
    renderer_classes = rest.DEFAULT_RENDERERS
    features = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = Elasticsearch(settings.ELASTIC_SEARCH_HOSTS)

    def authorized_queries(self, request: Request, analyzer) -> List[Search]:
        """
        Overide this method with custom authorization for your
        data
        """
        return []

    def autocomplete_queries(
            self, request, query: str, q_select: AbstractSet[str]):
        """provide autocomplete suggestions"""

        # get the relevant queries
        analyzer = QueryAnalyzer(query)
        query_components = select_queries(query, analyzer, q_select or set(), self.features)

        authorized_queries = self.authorized_queries(request, analyzer)
        # if you are authorized to look for names
        # add the query
        if authorized_queries:
            query_components.extend(authorized_queries)

        result_data = []

        # Ignoring cache in case debug is on
        ignore_cache = settings.DEBUG

        # create elk queries
        for search in query_components:  # type: Search
            search = search.using(self.client)

            log.debug(
                "Running query at %s: %s", search._index,
                json.dumps(search.to_dict(), indent=4)
            )

            # get the result from elastic
            try:
                result = search.execute(ignore_cache=ignore_cache)
            except TransportError as t:
                log.exception(
                    'FAILED ELK SEARCH: at %s %s', search._index,
                    json.dumps(search.to_dict(), indent=4))
                continue

            # Get the datas!
            result_data.append(result)

        return result_data

    def _get_uri(self, request, hit):
        # Retrieves the uri part for an item
        url = _get_url(request, hit)['self']['href']
        uri = urlparse(url).path[1:]
        return uri

    def _group_elk_results(self, request, results):
        """
        Group the elk results in their pretty name groups
        """
        flat_results = (hit for r in results for hit in r)
        result_groups = defaultdict(list)

        for hit in flat_results:
            group = _subtype_mapping[hit.subtype]
            display = hit._display
            if hit.subtype in _add_subtype_display:
                display += f' ({hit.subtype})'
            result_groups[group].append({
                '_display': display,
                'uri': self._get_uri(request, hit)
            })

        return result_groups

    @staticmethod
    def _kunstwerk_on_top(old_list: List) -> List:
        kunstwerk_index = 0
        new_list = []
        for item in old_list:
            if item['_display'].endswith('(kunstwerk)'):
                new_list.insert(kunstwerk_index, item)
                kunstwerk_index += 1
            else:
                new_list.append(item)
        return new_list

    def _order_results(self, results, request):
        """
        Group the elastic search results and order these groups

        @Params
        result - the elastic search result object
        query_string - the query string used to search for. This is for exact
                       match recognition
        """

        # put the elk results in subtype groups
        result_groups = self._group_elk_results(request, results)

        ordered_results = []

        for group in _autocomplete_group_order:
            if group not in result_groups:
                continue

            if group == 'Openbare ruimtes':
                result_groups[group] = self._kunstwerk_on_top(result_groups[group])

            size = _autocomplete_group_sizes[group]

            ordered_results.append({
                'label': group,
                'content': result_groups[group][:size],
                'total_results': len(result_groups[group])
            })

        return ordered_results

    def _abstr_list(self, request: Request, q_select: AbstractSet[str]):
        """
        returns result options
        ---
        parameters:
            - name: q
              description: givven search q give Result suggestions
              required: true
              type: string
              paramType: query
        """
        query = request.query_params.get('q')
        if 'features' in request.query_params:
            features = request.query_params['features']
            self.features = int(features) if features.isdigit() else 0

        if not query:
            return Response([])

        results = self.autocomplete_queries(request, query, q_select)
        response = self._order_results(results, request)

        return Response(response)


class BagQ(QFilter):

    search_description = 'Zoek in BAG'
    search_title = 'BAG object'


class TypeAheadBagViewSet(TypeaheadViewSet):

    filter_backends = [BagQ]

    def list(self, request):
        return self._abstr_list(request, {'bag', 'nummeraanduiding', 'pand'})


def authorized_subject_queries(request, analyzer) -> List[Search]:
    """
    Decide if which query we can execute

    public - no subjects
    employ - non natural subjects / nietnatuurlijk
    plus   - all subjects
    """

    authorized = request.is_authorized_for(authorization_levels.SCOPE_BRK_RSN)

    # Scope BRK/RSN or EMPLOYEE PLUS
    if authorized:
        return [brk_qs.kadastraal_subject_query(analyzer)]

    # Scope BRK/RS or EMPLOYEE
    niet_natuurlijk = brk_qs.kadastraal_subject_nietnatuurlijk_query
    authorized = request.is_authorized_for(authorization_levels.SCOPE_BRK_RS)

    if authorized:
        return [niet_natuurlijk(analyzer)]

    # NOT AUTHORIZED / PUBLIC
    return []


class BrkQ(QFilter):

    search_description = 'Zoek in BRK'
    search_title = 'BRK object'


class TypeAheadBrkViewSet(TypeaheadViewSet):
    """
    ### examples:

    *  input ?q= result
    *  AMR03                      =   AMR03
    *  amr03                      =   AMR03
    *  AMR03 B                    =   AMR03 B
    *  AMR03 b                    =   AMR03 B
    *  AMR03 B 334                =   AMR03 B 03347 G 0000
    *  AMR03 B 03347              =   AMR03 B 03347 G 0000
    *  AMR03 B 3347               =   AMR03 B 03347 G 0000
    *  AMR03 B 03347 G 0000       =   AMR03 B 03347 G 0000
    *  AMR03 B 05054 A 0002       =   AMR03 B 05054 A 0002
    *  AMR03 B 5054 A 2           =   AMR03 B 05054 A 0002
    *  AMR03 B 05054 0002         =   AMR03 B 05054 A 0002
    *  AMR03 B 5054 2             =   AMR03 B 05054 A 0002
    *  Aalsmeer B 03347           =   AMR03 B 03347 G 0000
    *  Aalsmeer B 3347            =   AMR03 B 03347 G 0000
    *  Aalsmeer B 03347 G 0000    =   AMR03 B 03347 G 0000
    *  Aalsmeer B 05054 A 0002    =   AMR03 B 05054 A 0002
    *  Aalsmeer B 5054 A 2        =   AMR03 B 05054 A 0002
    *  Aalsmeer B 05054 0002      =   AMR03 B 05054 A 0002
    *  Aalsmeer B 5054 2          =   AMR03 B 05054 A 0002
    *  AMR03 B 47                 =   AMR03 B 03347 G 0000
    *  Aalsmeer B 47              =   AMR03 B 03347 G 0000
    *  amsterdam f                =   ASD04 F
    *  sloten a                   =   STN02 A
    *  amsterdam a                =   ASD04 F 07587 A 0007
    *  amsterdam g                =   ASD04 F 03361 G 0000
    """

    filter_backends = [BrkQ]

    def authorized_queries(self, request, analyzer) -> List[Search]:
        return authorized_subject_queries(request, analyzer)

    def list(self, request):
        return self._abstr_list(request, {'brk'})


class GebiedTQ(QFilter):

    search_description = 'Zoek op gebied'
    search_title = 'Gebied'


class TypeAheadGebiedenViewSet(TypeaheadViewSet):

    filter_backends = [GebiedTQ]

    def list(self, request):
        return self._abstr_list(request, {'gebieden'})


class TypeAheadLegacyViewSet(TypeaheadViewSet):
    """
    The old typeahead containing all different results at once
    """

    def list(self, request):
        return self._abstr_list(request, set())


class SearchViewSet(viewsets.ViewSet):
    """
    Base class for ViewSets implementing search.
    """

    metadata_class = QueryMetadata
    page_size = 100
    url_name = 'search-list'
    page_limit = 10
    features = 0

    renderer_classes = rest.DEFAULT_RENDERERS
    filter_backends = [QFilter]

    def search_query(self, request,
                     elk_client, analyzer: QueryAnalyzer) -> Search:
        """
        Construct the search query that is executed by this view set.
        """
        raise NotImplementedError

    def _set_followup_url(self, request, result, end,
                          response, query, page):
        """
        Add paging links for result set to response object
        """

        # make query url friendly again
        url_query = quote(query)
        # Finding link to self via reverse url search
        followup_url = reverse(self.url_name, request=request)

        separator = '&' if '?' in followup_url else '?'
        self_url = f"{followup_url}{separator}q={url_query}&page={page}"

        response['_links'] = OrderedDict([
            ('self', {'href': self_url}),
            ('next', {'href': None}),
            ('prev', {'href': None})
        ])

        # Finding and setting prev and next pages
        if end < result.hits.total:
            if end < (self.page_size * self.page_limit):
                # There should be a next
                response['_links']['next']['href'] = f"{followup_url}{separator}q={url_query}&page={page + 1}"
        if page == 2:
            response['_links']['prev']['href'] = f"{followup_url}{separator}q={url_query}"
        elif page > 2:
            response['_links']['prev']['href'] = f"{followup_url}{separator}q={url_query}&page={page - 1}"

    def list(self, request, *args, **kwargs):
        """
        Create a response list of search items

        ---
        parameters:
            - name: q
              description: Zoek object
              required: true
        """

        if 'q' not in request.query_params:
            return Response([])

        if 'features' in request.query_params:
            features = request.query_params['features']
            self.features = int(features) if features.isdigit() else 0

        page = 1
        if 'page' in request.query_params:
            # limit search results pageing in elastic is slow
            page = int(request.query_params['page'])
            if page > self.page_limit:
                page = self.page_limit

        start = ((page - 1) * self.page_size)
        end = (page * self.page_size)

        query = request.query_params['q']
        analyzer = QueryAnalyzer(query)

        elk_client = Elasticsearch(
            settings.ELASTIC_SEARCH_HOSTS,
            raise_on_error=True
        )

        # get the result from elastic
        elk_query = self.search_query(request, elk_client, analyzer)

        search = elk_query[start:end]

        if not search:
            log.debug('no elk query')
            return Response([])

        ignore_cache = settings.DEBUG

        log.debug(
            "Running query at %s: %s", search._index,
            json.dumps(search.to_dict(), indent=4)
        )

        try:
            result = search.execute(ignore_cache=ignore_cache)
        except TransportError:
            log.exception("Could not execute search query at %s: %s", search._index, query)
            log.debug(json.dumps(search.to_dict(), indent=4))
            return Response([], 500)

        response = OrderedDict()

        # log.exception(json.dumps(result.to_dict(), indent=4))

        self._set_followup_url(request, result, end, response, query, page)

        count = result.hits.total
        response['count_hits'] = count
        response['count'] = count

        results = [self.normalize_hit(h, request) for h in result.hits]
        response['results'] = self.list_results(results)

        return Response(response)

    def list_results(self, results):
        return results

    def get_url(self, request, hit):
        """
        For each hit determine its resource url
        """
        return _get_url(request, hit)

    def get_hit_data(self, result, hit):
        result.update(hit.to_dict())

    def normalize_hit(self, hit, request):
        result = OrderedDict()
        result['_links'] = self.get_url(request, hit)
        if 'order' in hit:
            del(hit['order'])

        if hit.subtype:
            result['type'] = hit.subtype
        else:
            result['type'] = hit.meta.doc_type

        result['dataset'] = hit.meta.index

        self.get_hit_data(result, hit)

        return result


class KadastraalSubjectQ(QFilter):

    search_description = 'Zoek op kadastrale subjecten'
    search_title = 'Kadastraal subject'


class SearchSubjectViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    kadastraal subjects (VVE, personen) objects
    that match the elastic search query.

    Een Kadastraal Subject is een persoon die
    in de kadastrale registratie voorkomt.
    Het betreft hier zowel natuurlijk- als niet natuurlijk personen.

    https://www.amsterdam.nl/stelselpedia/brk-index/catalog-brk-levering/kadastraal-subject/

    """

    url_name = 'search/kadastraalsubject-list'
    filter_backends = [KadastraalSubjectQ]

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> Search:
        """
        Execute search on Subject
        """

        querylist = authorized_subject_queries(request, analyzer)

        if not querylist:
            raise PermissionDenied

        # authorized only!
        search = querylist[0].using(elk_client)

        return search


class KadastraalObjectQ(QFilter):

    search_description = 'Zoek op kadastrale objecten'
    search_title = 'Kadastraal object'


class SearchObjectViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    grond percelen objects that match the elastic search query.

    ### examples:


    *  input ?q= result
    *  AMR03                      =   AMR03
    *  amr03                      =   AMR03
    *  AMR03 B                    =   AMR03 B
    *  AMR03 b                    =   AMR03 B
    *  AMR03 B 334                =   AMR03 B 03347 G 0000
    *  AMR03 B 03347              =   AMR03 B 03347 G 0000
    *  AMR03 B 3347               =   AMR03 B 03347 G 0000
    *  AMR03 B 03347 G 0000       =   AMR03 B 03347 G 0000
    *  AMR03 B 05054 A 0002       =   AMR03 B 05054 A 0002
    *  AMR03 B 5054 A 2           =   AMR03 B 05054 A 0002
    *  AMR03 B 05054 0002         =   AMR03 B 05054 A 0002
    *  AMR03 B 5054 2             =   AMR03 B 05054 A 0002
    *  Aalsmeer B 03347           =   AMR03 B 03347 G 0000
    *  Aalsmeer B 3347            =   AMR03 B 03347 G 0000
    *  Aalsmeer B 03347 G 0000    =   AMR03 B 03347 G 0000
    *  Aalsmeer B 05054 A 0002    =   AMR03 B 05054 A 0002
    *  Aalsmeer B 5054 A 2        =   AMR03 B 05054 A 0002
    *  Aalsmeer B 05054 0002      =   AMR03 B 05054 A 0002
    *  Aalsmeer B 5054 2          =   AMR03 B 05054 A 0002
    *  AMR03 B 47                 =   AMR03 B 03347 G 0000
    *  Aalsmeer B 47              =   AMR03 B 03347 G 0000
    *  amsterdam f                =   ASD04 F
    *  sloten a                   =   STN02 A
    *  amsterdam a                =   ASD04 F 07587 A 0007
    *  amsterdam g                =   ASD04 F 03361 G 0000

    """

    url_name = 'search/kadastraalobject-list'
    filter_backends = [KadastraalObjectQ]

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> List[Search]:
        """
        Execute search in Objects
        """
        if not analyzer.is_kadastraal_object_prefix():
            return []

        search_q = brk_qs.kadastraal_object_query(analyzer)
        search = search_q.using(elk_client)
        return search


class BouwblokQ(QFilter):

    search_description = 'Zoek op bouwblokken'
    search_title = 'Bouwblok'


class SearchBouwblokViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    grond percelen objects that match the elastic search query.
    """

    url_name = 'search/bouwblok-list'
    filter_backends = [BouwblokQ]

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> Search:
        """
        Execute search in Objects
        """
        if not analyzer.is_bouwblok_prefix():
            return []

        search_q = bag_qs.bouwblok_query(analyzer)
        search = search_q.using(elk_client)

        return search.filter('terms', subtype=['bouwblok'])


class GebiedQ(QFilter):

    search_description = 'Zoek op gebieden'
    search_title = 'Gebied'


class SearchGebiedenViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    grond percelen objects that match the elastic search query.
    """

    url_name = 'search/gebied-list'
    filter_backends = [GebiedQ]

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> Search:
        """
        Execute search in Objects
        """

        if analyzer.is_bouwblok_prefix():
            search = bag_qs.bouwblok_query(analyzer)
            search = search.using(elk_client)
            return search
        else:
            search = bag_qs.gebied_query(analyzer).using(elk_client)

        return search


class OpenbareRuimteQ(QFilter):

    search_description = 'Zoek op openbare ruimtes'
    search_title = 'Openbare ruimte'


def _subtype_contains_weg(subtype):
    return subtype is None or subtype == 'weg' or (subtype[0:4] == 'not_' and subtype[4:] != 'weg')


class SearchOpenbareRuimteViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset
    of all openbare ruimte objects that match the elastic search query.

    The optional parameter `subtype` limits the query to a openbare ruimte
    of a specific subtype, or, if the negation was specified with for example
    `subtype=not_weg` all subtypes except `weg` are returned.

    Een OPENBARE RUIMTE is een door het bevoegde gemeentelijke orgaan als
    zodanig aangewezen en van een naam voorziene
    buitenruimte die binnen één woonplaats is gelegen.

    Als openbare ruimte worden onder meer aangemerkt weg, water,
    terrein, spoorbaan en landschappelijk gebied.

    http://www.amsterdam.nl/stelselpedia/bag-index/catalogus-bag/objectklasse-3/

    """
    url_name = 'search/openbareruimte-list'
    filter_backends = [OpenbareRuimteQ]

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> Search:
        """
        Execute search in Objects
        """
        if 'subtype' in request.query_params:
            subtype = request.query_params['subtype']
            if not re.match("^[a-z_]{3,30}$", subtype):
                subtype = None
        else:
            subtype = None

        if analyzer.is_postcode_prefix() and _subtype_contains_weg(subtype):
            search_data = bag_qs.postcode_query(analyzer)
        elif analyzer.is_landelijk_id_prefix():
            search_data = bag_qs.landelijk_id_openbare_ruimte_query(analyzer, subtype)
        else:
            search_data = bag_qs.openbare_ruimte_query(analyzer, self.features, subtype)

        return search_data.using(elk_client)

    def list_results(self, old_results: List) -> List:
        new_results = []
        # Put subtype kunstwerk on top of list
        subtype_index = 0
        for result in old_results:
            if result['subtype'] == 'kunstwerk':
                new_results.insert(subtype_index, result)
                subtype_index += 1
            else:
                new_results.append(result)
        return new_results


class NummeraanduidingQ(QFilter):

    search_description = 'Zoek op adressen'
    search_title = 'Adres'


class SearchNummeraanduidingViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset
    of nummeraanduiding objects that match the elastic search query.

    [/search/adres/?q=silodam 340](https://api.data.amsterdam.nl/atlas/search/adres/?q=silodam 340)

    Een nummeraanduiding, in de volksmond ook wel adres genoemd, is een door
    het bevoegde gemeentelijke orgaan als
    zodanig toegekende aanduiding van een verblijfsobject,
    standplaats of ligplaats.

    http://www.amsterdam.nl/stelselpedia/bag-index/catalogus-bag/objectklasse-2/

    LET OP !!  toevoeging is de toevoeging achter een straatnaam !!

    gebruik:

    bag_toevoeging is toevoeging na huisnummer.
    bag_huisletter
    -----

    gebruik

    straatnaam huisnummer

    of
    ==

    straatnaam toevoeging, als er meer dan een huisnummer betrokken is bij
    het adres / nummeraanduiding.

    Het is ook mogelijk om te zoeken op prefix van het landelijk_id van nummeraanduiding of bijbehorend
    verblijfsobject, ligplaats of standplaats.

    [/search/adres/?q=03630100010317](https://api.data.amsterdam.nl/atlas/search/adres/?q=03630100010317)

    of

    [/search/adres/?q=3630100](https://api.data.amsterdam.nl/atlas/search/adres/?q=3630100)


    """   # noqa
    url_name = 'search/adres-list'
    filter_backends = [NummeraanduidingQ]
    custom_sort = True

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> Search:
        """
        Execute search in Objects
        """
        q = None

        if analyzer.is_postcode_huisnummer_prefix():
            q = bag_qs.postcode_huisnummer_query(analyzer)

        elif analyzer.is_straatnaam_huisnummer_prefix():
            q = bag_qs.straatnaam_huisnummer_query(analyzer, self.features)


        elif analyzer.is_landelijk_id_prefix():
            q = bag_qs.landelijk_id_nummeraanduiding_query(analyzer)

        if not q:
            q = bag_qs.straatnaam_query(analyzer)

        # default response search roads
        return q.using(elk_client)

    def get_hit_data(self, result, hit):
        """
        Remove attribute fields not needed for enduser
        """
        for key, value in hit.to_dict().items():
            if key.startswith('comp_'):
                continue
            if key.endswith('_keyword'):
                continue
            if key.endswith('_nen'):
                continue
            result[key] = value


class PostcodeQ(QFilter):

    search_description = 'Zoek op postcodes'
    search_title = 'Postcode'


class SearchPostcodeViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset
    of nummeraanduiding objects that match the elastic search query.

    voorbeeld:

    [/search/postcode/?q=1013AW](https://api.data.amsterdam.nl/atlas/search/postcode/?q=1013AW)

    Een nummeraanduiding, in de volksmond ook wel adres genoemd, is een door
    het bevoegde gemeentelijke orgaan als
    zodanig toegekende aanduiding van een verblijfsobject,
    standplaats of ligplaats.

    http://www.amsterdam.nl/stelselpedia/bag-index/catalogus-bag/objectklasse-2/

    """
    url_name = 'search/postcode-list'
    filter_backends = [PostcodeQ]

    def search_query(self, request, elk_client,
                     analyzer: QueryAnalyzer) -> Search:
        """Creating the actual query to ES"""

        if analyzer.is_postcode_huisnummer_prefix():
            return bag_qs.postcode_huisnummer_query(analyzer).using(elk_client)

        elif analyzer.is_postcode_prefix():
            search = bag_qs.postcode_query(analyzer)
            return search.using(elk_client)

        return []


class PandQ(QFilter):
    search_description = 'Zoek op pand'
    search_title = 'Pand'


class SearchPandViewSet(SearchViewSet):
    url_name = 'search/pand-list'
    filter_backends = [PandQ]

    def search_query(self, request,
                     elk_client, analyzer: QueryAnalyzer) -> Search:
        if analyzer.is_landelijk_id_prefix():
            return bag_qs.landelijk_id_pand_query(analyzer).using(elk_client)
        else:
            return bag_qs.pandnaam_query(analyzer).using(elk_client)

        return []
