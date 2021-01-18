"""
==================================================
 Individual search queries
--------------------------------------------------
 Each of these functions builds a query and,
 if needed an aggregation as well.
 They all return a dict with the Q and A keyes
==================================================
"""

# Python
import logging

from django.conf import settings
from elasticsearch_dsl import Q, Search

from search.queries import create_search_query
from search.query_analyzer import QueryAnalyzer

log = logging.getLogger('bag_Q')

BAG_BOUWBLOK = settings.ELASTIC_INDICES['BAG_BOUWBLOK']
BAG_GEBIED = settings.ELASTIC_INDICES['BAG_GEBIED']
NUMMERAANDUIDING = settings.ELASTIC_INDICES['NUMMERAANDUIDING']
BAG_PAND = settings.ELASTIC_INDICES['BAG_PAND']


def postcode_huisnummer_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """Create query/aggregation for postcode house number search"""

    postcode, huisnummer, toevoeging = \
        analyzer.get_postcode_huisnummer_toevoeging()

    return create_search_query(
        query={
            'bool': {
                'must': [
                    {
                        'prefix': {
                            'postcode.raw': postcode,
                        }
                    },
                    {
                        'prefix': {
                            'toevoeging': toevoeging,
                        }
                    },
                ],
            },
        },
        indexes=[NUMMERAANDUIDING],
        sort_fields=['straatnaam.raw', 'huisnummer', 'toevoeging.keyword']
    )


def postcode_huisnummer_exact_query(analyzer: QueryAnalyzer) -> Search:
    """Create query/aggregation for postcode house number search"""

    postcode, huisnummer, toevoeging = \
        analyzer.get_postcode_huisnummer_toevoeging()

    return create_search_query(
        query=Q(
            'bool',
            must=[
                Q('term', postcode=postcode),
                Q('match_phrase', toevoeging=toevoeging),
                Q('term', huisnummer=huisnummer)
            ],
        ),
        sort_fields=['straatnaam.raw', 'huisnummer', 'toevoeging.keyword'],
        indexes=[NUMMERAANDUIDING],
        size=1
    )


def bouwblok_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """ Create query/aggregation for bouwblok search"""
    return create_search_query(
        query={
            "prefix": {
                "code": analyzer.get_bouwblok()
            },
        },
        sort_fields=['code.keyword'],
        indexes=[BAG_BOUWBLOK],
    )


def postcode_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """ create query/aggregation for public area"""

    postcode = analyzer.get_postcode()

    return create_search_query(
        query=Q(
            'bool',
            must=[
                {'prefix': {'postcode': postcode}},
                Q('term', subtype='weg'),
            ],
        ),
        sort_fields=['naam.keyword'],
        indexes=[BAG_GEBIED]
    )


def _basis_openbare_ruimte_query(
        analyzer: QueryAnalyzer,
        features: int = 0,
        must: [dict] = None,
        must_not: [dict] = None,
        useorder: [bool] = False) -> Search:
    """
    Basis openbare-ruimte query.

    Het resultaat ordent pure prefix matches vóór phrase_prefix matches.
    """

    # Logica:
    # Het doel is om 'echte' prefix-matches te sorteren vóór phrase-prefix
    # matches.  Met alleen phrase-prefix kan dat niet, dus we gebruiken twee
    # 'should' queries waarvan er minimaal één moet matchen. Met de
    # constant_score wrapper zorgen we ervoor dat alle 'prefix' matches een
    # score van 10 krijgen, en alle 'phrase_prefix' matches een score van 5.
    # De 'constant_score' op de 'must' voorkomt dat die in de weg zit.  Op
    # basis van deze output kunnen we vervolgens ordenen op score, gevolgd
    # door naam.
    #
    # Voorbeelden: Zoeken op Weesp, geeft eerst Weesperstraat, dan pas
    # Metrostation Weesperstraat.  Zoeken op Prinsen, geeft eerst
    # Prinsengracht, dan pas Korte Prinsengracht.

    _must = [{'constant_score': {'filter': q}} for q in (must or [])]
    _must_not = [{'constant_score': {'filter': q}} for q in (must_not or [])]

    sort_fields = ['_score', 'naam.keyword']

    _fields = ['naam', 'naam_nen', 'postcode', 'naam_no_ws']

    if useorder:
        sort_fields = ['order', 'naam.keyword']

    straat_naam = analyzer.get_straatnaam()

    query = {
        'bool': {
            'must': _must,
            'must_not': _must_not,
            'should': [
                {
                    'constant_score': {
                        'filter': {
                            'prefix': {
                                'naam.keyword': straat_naam,
                            }
                        },
                        'boost': 10,
                    },
                },
                {
                    'constant_score': {
                        'filter': {
                            'multi_match': {
                                'query': straat_naam,
                                'type': 'phrase_prefix',
                                'fields': _fields
                            }
                        },
                        'boost': 5,
                    }
                }
            ],
            'minimum_should_match': 1,
        }
    }

    if not features & settings.FEATURE_2:  # By default only Amsterdam = 0363
        query['bool']['filter'] = {
            'prefix': {
                'landelijk_id.raw': '0363'
            }
        }

    return create_search_query(
        query=query,
        indexes=[BAG_GEBIED],
        sort_fields=sort_fields,
        size=100,
    )


def weg_query(analyzer: QueryAnalyzer) -> Search:
    """
    Maak een query voor openbare ruimtes van het type 'weg'.
    """

    return _basis_openbare_ruimte_query(
        analyzer,
        must=[{'term': {'subtype': 'weg'}}]
    )


def _add_subtype(q : dict, subtype: str):
    if subtype:
        if subtype.startswith("not_"):
            subtype = subtype[4:]
            q['must_not'] = [{'term': {'subtype': subtype}}]
        else:
            q['must'].append({'term': {'subtype': subtype}})


def openbare_ruimte_query(analyzer: QueryAnalyzer, features: int = 0, subtype: str = None) -> Search:
    """
    Maak een query voor openbare ruimte.
    """
    dq = {
        'must': [{'term': {'type': 'openbare_ruimte'}}]
    }

    _add_subtype(dq, subtype)
    return _basis_openbare_ruimte_query(analyzer, features, **dq)


def gebied_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """
    Maak een query voor gebieden.
    """
    return _basis_openbare_ruimte_query(
        analyzer, useorder=False, must=[{
            'term': {'type': 'gebied'},
        }],
    )


def straatnaam_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    street_part = analyzer.get_straatnaam()
    query = {
        'bool': {
            'must': {
                'multi_match': {
                    'query': street_part,
                    'type': 'phrase_prefix',
                    'fields': [
                        'straatnaam',
                        'straatnaam_nen',
                        'straatnaam_no_ws'
                    ]
                }
            }
        }
    }

    if not features & settings.FEATURE_2:  # By default only Amsterdam = 0363
        query['bool']['filter'] = {
            'prefix': {
                'landelijk_id.raw': '0363'
            }
        }

    return create_search_query(
        query=query,
        sort_fields=['straatnaam.raw', 'huisnummer', 'toevoeging.keyword'],
        indexes=[NUMMERAANDUIDING]
    )


def straatnaam_huisnummer_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:

    straat, huisnummer, toevoeging = \
        analyzer.get_straatnaam_huisnummer_toevoeging()
    query = {
        'bool': {
            'must': {
                'prefix': {
                    'toevoeging': toevoeging,
                }
            },
            'should': [
                {
                    'match': {
                        'straatnaam_keyword': straat
                    }
                },
                {
                    'multi_match': {
                        'query': straat,
                        'type': 'phrase_prefix',
                        'fields': [
                            'straatnaam',
                            'straatnaam_nen',
                            'straatnaam_no_ws'
                        ]
                    },
                },

            ],
            'minimum_should_match': 1,
        },
    }

    if not features & settings.FEATURE_2:  # By default only Amsterdam = 0363
        query['bool']['filter'] = {
            'prefix': {
                'landelijk_id.raw': '0363'
            }
        }

    return create_search_query(
        query=query,
        sort_fields=['_score', 'straatnaam.raw', 'huisnummer', 'toevoeging.keyword'],
        indexes=[NUMMERAANDUIDING],
        search_type="dfs_query_then_fetch"
    )


def landelijk_id_nummeraanduiding_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """ create query/aggregation for public area"""

    landelijk_id = analyzer.get_landelijk_id()

    return create_search_query(
        query=Q(
            'bool',
            should=[
                {'prefix': {'landelijk_id.nozero': landelijk_id}},
                {'prefix': {'adresseerbaar_object_id.nozero': landelijk_id}}
            ],
        ),
        sort_fields=['_id'],
        indexes=[NUMMERAANDUIDING]
    )


def landelijk_id_openbare_ruimte_query(analyzer: QueryAnalyzer, features: int = 0, subtype: str = None) -> Search:
    """ create query/aggregation for public area"""

    landelijk_id = analyzer.get_landelijk_id()

    kwargs = {
            'must' : [
                {'term': {'type': 'openbare_ruimte'}},
                {'prefix': {'landelijk_id.nozero': landelijk_id}},
            ]
    }
    _add_subtype(kwargs, subtype)

    query = Q(
            'bool',
            **kwargs
        )

    return create_search_query(
        query=query,
        sort_fields=['_id'],
        indexes=[BAG_GEBIED]
    )


def landelijk_id_pand_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """ create query/aggregation for public area"""

    landelijk_id = analyzer.get_landelijk_id()

    return create_search_query(
        query=Q(
            'bool',
            must=[
                {'prefix': {'landelijk_id.nozero': landelijk_id}},
            ]
        ),
        sort_fields=['_id'],
        indexes=[BAG_PAND]
    )


def pandnaam_query(analyzer: QueryAnalyzer, features: int = 0) -> Search:
    """
    Maak een query voor pand op pandnaam.
    """
    pandnaam = analyzer.get_straatnaam()
    query = {
        'bool': {
            'must': {
                'multi_match': {
                    'query': pandnaam,
                    'type': 'phrase_prefix',
                    'fields': [
                        'pandnaam',
                    ]
                }
            }
        }
    }

    if not features & settings.FEATURE_2:  # By default only Amsterdam = 0363
        query['bool']['filter'] = {
            'prefix': {
                'landelijk_id.raw': '0363'
            }
        }

    return create_search_query(
        query=query,
        sort_fields=['_display'],
        indexes=[BAG_PAND]
    )
