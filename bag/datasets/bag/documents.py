# Python
# Packages

import elasticsearch_dsl as es
from django.conf import settings

from search import analyzers
from . import models


naam_fields = {
    'raw': es.Keyword(normalizer=analyzers.lowercase),
    'ngram': es.Text(
        analyzer=analyzers.autocomplete, search_analyzer='standard'),
}

postcode_fields = {
    'raw': es.Keyword(normalizer=analyzers.lowercase),
    'ngram': es.Text(
        analyzer=analyzers.autocomplete, search_analyzer='standard'),
}


text_fields = {
    'ngram_edge': es.Text(
        analyzer=analyzers.autocomplete, search_analyzer='standard'
    ),
    'keyword': es.Keyword(normalizer=analyzers.lowercase),
}


class Nummeraanduiding(es.DocType):
    """
    All bag objects should have one or more adresses

    Een nummeraanduiding, in de volksmond ook wel adres genoemd, is een door
    het bevoegde gemeentelijke orgaan als
    zodanig toegekende aanduiding van een verblijfsobject, standplaats of
    ligplaats.

    [Stelselpedia](http://www.amsterdam.nl/stelselpedia/bag-index/catalogus-bag/objectklasse-2/)
    """
    straatnaam = es.Text(
        analyzer=analyzers.adres,
        fields={
            'raw': es.Keyword(),
            'ngram_edge': es.Text(
                analyzer=analyzers.autocomplete, search_analyzer='standard'
            )
        }
    )

    straatnaam_keyword = es.Keyword(normalizer=analyzers.lowercase)

    straatnaam_nen = es.Text(
        analyzer=analyzers.adres,
        fields={
            'raw': es.Keyword(),
            'ngram_edge': es.Text(
                analyzer=analyzers.autocomplete, search_analyzer='standard'
            )
        }
    )

    straatnaam_no_ws = es.Text(analyzer=analyzers.straat_no_ws)
    straatnaam_nen_keyword = es.Keyword(normalizer=analyzers.lowercase)

    adres = es.Text(
        analyzer=analyzers.adres,
        fields={
            'raw': es.Keyword(),
            'ngram_edge': es.Text(
                analyzer=analyzers.autocomplete, search_analyzer='standard'
            )
        }
    )

    huisnummer = es.Integer(
        fields={'variation': es.Text(analyzer=analyzers.huisnummer)})

    toevoeging = es.Text(
        analyzer=analyzers.toevoeging,
        fields={'keyword': es.Keyword()}
    )

    # to return official bag fields
    bag_toevoeging = es.Keyword()
    bag_huisletter = es.Keyword()
    woonplaats = es.Keyword()

    postcode = es.Text(
        analyzer=analyzers.postcode,
        fields=postcode_fields,
    )

    order = es.Integer()

    type_adres = es.Keyword()
    status = es.Text()
    vbo_status = es.Text()

    subtype = es.Keyword()
    _display = es.Keyword()

    landelijk_id = es.Text(
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.Keyword(),
            'nozero': es.Text(analyzer=analyzers.nozero)
        }
    )
    adresseerbaar_object_id = es.Text(  # Is landelijk_id for related verblijfsobject, ligplaats of standplaats
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.Keyword(),
            'nozero': es.Text(analyzer=analyzers.nozero)
        }
    )

    class Index:
        name = settings.ELASTIC_INDICES['NUMMERAANDUIDING']


class Bouwblok(es.DocType):
    """
    Bouwblok searchable fields.
    """
    code = es.Text(
        analyzer=analyzers.bouwblokid,
        fields={
            'keyword': es.Keyword()
        },
    )

    subtype = es.Keyword()

    _display = es.Keyword()

    class Index:
        name = settings.ELASTIC_INDICES['BAG_BOUWBLOK']


class Gebied(es.DocType):
    """
    Een vindbaar gebied

    Unesco
    Buurt
    Buurtcombinatie
    Stadsdeel
    Grootstedelijk
    Gemeente
    Woonplaats
    """

    id = es.Keyword()

    _display = es.Keyword()

    naam = es.Text(
        analyzer=analyzers.adres,
        fields=text_fields
    )

    naam_nen = es.Text(
        analyzer=analyzers.adres,
        fields=text_fields
    )

    naam_no_ws = es.Text(
        analyzer=analyzers.straat_no_ws,
        fields=text_fields
    )

    postcode = es.Text(
        analyzer=analyzers.postcode,
        fields=postcode_fields
    )

    g_code = es.Text(
        analyzer=analyzers.autocomplete,
        search_analyzer='standard',
        fields={
            'keyword': es.Keyword(),
            'ngram': es.Text(
                analyzer=analyzers.autocomplete),
        }
    )

    # gebied order
    order = es.Integer()

    subtype = es.Keyword()
    type = es.Keyword()

    centroid = es.GeoPoint()

    landelijk_id = es.Text(  # Only for voor openbare_ruimte
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.Keyword(),
            'nozero': es.Text(analyzer=analyzers.nozero)
        }
    )

    gsg_type = es.Keyword()

    class Index:
        name = settings.ELASTIC_INDICES['BAG_GEBIED']


class Pand(es.DocType):
    id = es.Keyword()
    landelijk_id = es.Text(
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.Keyword(),
            'nozero': es.Text(analyzer=analyzers.nozero)
        }
    )
    pandnaam = es.Text(
        analyzer=analyzers.adres,
        fields=naam_fields
    )
    _display = es.Keyword()

    class Index:
        name = settings.ELASTIC_INDICES['BAG_PAND']


def get_centroid(geom, transform=None):
    """
    Finds the centroid of a geometrie object
    An optional transform string can be given noting
    the name of the system to translate to, i.e. 'wgs84'
    """
    if not geom:
        return None

    result = geom.centroid
    if transform:
        result.transform(transform)
    return result.coords


def add_verblijfsobject(doc, vo: models.Verblijfsobject):
    if vo:
        doc.centroid = get_centroid(vo.geometrie, 'wgs84')
        doc.subtype_id = vo.id
        doc.order = analyzers.orderings['adres']


def add_standplaats(doc, sp: models.Standplaats):
    if sp:
        doc.centroid = get_centroid(sp.geometrie, 'wgs84')
        doc.subtype_id = sp.id
        doc.order = analyzers.orderings['adres']


def add_ligplaats(doc, lp: models.Ligplaats):
    if lp:
        doc.centroid = get_centroid(lp.geometrie, 'wgs84')
        doc.subtype_id = lp.id
        doc.order = analyzers.orderings['adres']


def from_bouwblok(n: models.Bouwblok):
    doc = Bouwblok(_id=n.id)
    doc.code = n.code
    doc.subtype = 'bouwblok'
    doc._display = '{} (bouwblok)'.format(n.code)
    return doc


def from_nummeraanduiding_ruimte(n: models.Nummeraanduiding) -> Nummeraanduiding:
    openbare_ruimte = n.openbare_ruimte
    adresseerbaar_object = n.adresseerbaar_object

    doc = Nummeraanduiding(_id=n.id)
    doc.adres = n.adres()
    doc.postcode = n.postcode
    doc.straatnaam = openbare_ruimte.naam
    doc.straatnaam_no_ws = openbare_ruimte.naam
    doc.straatnaam_nen = openbare_ruimte.naam_nen
    doc.straatnaam_keyword = openbare_ruimte.naam
    doc.straatnaam_nen_keyword = openbare_ruimte.naam_nen
    doc.huisnummer = n.huisnummer
    doc.toevoeging = n.toevoeging

    doc.bag_huisletter = n.huisletter
    doc.bag_toevoeging = n.huisnummer_toevoeging
    doc.woonplaats = n.woonplaats.naam

    doc.type_adres = n.type_adres
    doc.status = n.status
    doc.landelijk_id = n.landelijk_id

    # verblijfsobject status
    if adresseerbaar_object:
        doc.vbo_status = adresseerbaar_object.status
        doc.adresseerbaar_object_id = adresseerbaar_object.landelijk_id

    if n.bron_id:
        doc.bron = n.bron.omschrijving

    # if not doc.subtype:
    #    return doc

    doc.subtype = n.get_type_display().lower()

    if doc.subtype == 'verblijfsobject':
        add_verblijfsobject(doc, n.verblijfsobject)
    elif doc.subtype == 'standplaats':
        add_standplaats(doc, n.standplaats)
    elif doc.subtype == 'ligplaats':
        add_ligplaats(doc, n.ligplaats)
    elif doc.subtype == 'overig gebouwd object':
        pass
    elif doc.subtype == 'overig terrein':
        pass

    doc._display = n.adres()
    if n.landelijk_id.startswith("0457"):  # Weesp
        # TODO : Only add Weesp if openbare_ruimte naam exists for Amsterdam
        doc._display += " (Weesp)"

    return doc


def from_openbare_ruimte(o: models.OpenbareRuimte):
    d = Gebied(_id='opr_{}'.format(o.id))
    d.type = 'openbare_ruimte'

    # weg, water, spoorbaan, terrein, kunstwerk (brug), landschap,..
    d.subtype = o.get_type_display().lower()
    d.subtype_id = o.id

    d.naam = o.naam
    d.naam_nen = o.naam_nen
    d.naam_no_ws = o.naam

    postcodes = set()

    for a in o.adressen.all():
        if a.postcode:
            postcodes.add(a.postcode)

    d.postcode = list(postcodes)
    d.order = analyzers.orderings['openbare_ruimte']
    d._display = d.naam
    if o.landelijk_id.startswith("0457"):  # Weesp
        # TODO : Only add Weesp if openbare_ruimte naam exists for Amsterdam
        d._display += " (Weesp)"

    d.centroid = get_centroid(o.geometrie, 'wgs84')

    d.landelijk_id = o.landelijk_id

    return d


def from_unesco(u: models.Unesco):
    d = Gebied(_id='unseco{}'.format(u.id))

    d.type = 'gebied'

    d.subtype = 'unesco'

    d._display = '{} ({})'.format(u.naam, d.subtype)

    d.subtype_id = u.id
    d.naam = u.naam
    d.centroid = get_centroid(u.geometrie, 'wgs84')
    d.order = 1
    return d


def from_buurt(b: models.Buurt):
    d = Gebied(_id='buurt{}'.format(b.id))
    d.subtype = 'buurt'
    d.type = 'gebied'

    d.subtype_id = b.id
    d.naam = b.naam
    d._display = '{} ({})'.format(b.naam, d.subtype)
    d.g_code = b.code
    d.centroid = get_centroid(b.geometrie, 'wgs84')
    d.order = 6
    return d


def from_buurtcombinatie(bc: models.Buurtcombinatie):
    d = Gebied(_id='buurtcombinatie{}'.format(bc.id))
    d.subtype = 'buurtcombinatie'
    d.type = 'gebied'

    d.subtype_id = bc.id
    d.naam = bc.naam
    d._display = '{} ({})'.format(bc.naam, 'wijk')
    d.g_code = bc.code
    d.order = 5
    d.centroid = get_centroid(bc.geometrie, 'wgs84')
    return d


def from_gebiedsgerichtwerken(gg: models.Gebiedsgerichtwerken):
    d = Gebied(_id='gebiedsgericht{}'.format(gg.id))
    d.subtype = 'gebiedsgerichtwerken'
    d.type = 'gebied'

    d.subtype_id = gg.id
    d.naam = gg.naam
    d._display = '{} ({})'.format(gg.naam, 'gebiedsgericht werken')
    d.g_code = gg.code
    d.centroid = get_centroid(gg.geometrie, 'wgs84')
    d.order = 4
    return d


def from_stadsdeel(sd: models.Stadsdeel):
    d = Gebied(_id='stadsdeel{}'.format(sd.id))
    d.subtype = 'stadsdeel'
    d.type = 'gebied'

    d.subtype_id = sd.id
    d.naam = sd.naam
    d._display = '{} ({})'.format(sd.naam, d.subtype)
    d.g_code = sd.code
    d.order = 3
    d.centroid = get_centroid(sd.geometrie, 'wgs84')
    return d


def from_grootstedelijk(gs: models.Grootstedelijkgebied):
    d = Gebied(_id='stadsdeel{}'.format(gs.id))
    d.subtype = 'grootstedelijk'
    d.type = 'gebied'

    d.subtype_id = gs.id
    d.naam = gs.naam
    d.gsg_type = gs.gsg_type
    d._display = '{} ({})'.format(gs.naam, 'grootstedelijk gebied')
    d.centroid = get_centroid(gs.geometrie, 'wgs84')
    d.order = 2
    return d


def from_gemeente(g: models.Gemeente):
    d = Gebied(_id='gemeente{}'.format(g.id))
    d.subtype = 'gemeente'
    d.type = 'gebied'

    d.subtype_id = g.naam.lower()
    d.naam = g.naam
    d._display = '{} ({})'.format(g.naam, d.subtype)
    d.g_code = g.code
    d.order = 1
    return d


def from_woonplaats(w: models.Woonplaats):
    d = Gebied(_id='woonplaats{}'.format(w.id))
    d.subtype = 'woonplaats'
    d.type = 'gebied'

    d.subtype_id = w.id
    d.naam = w.naam
    d._display = '{} ({})'.format(w.naam, d.subtype)
    d.landelijk_id = w.landelijk_id
    d.g_code = w.landelijk_id
    d.order = 2
    return d


def from_pand(l):
    d = Pand(_id=l.id)
    d.type = 'pand'
    d.subtype = 'pand'
    d.landelijk_id = l.landelijk_id
    d.pandnaam = l.pandnaam
    d._display = '{}'.format(l.pandnaam if l.pandnaam else l.landelijk_id)
    return d
