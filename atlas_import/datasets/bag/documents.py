import elasticsearch_dsl as es

from . import models
from datasets.generic import analyzers
from django.conf import settings


class Ligplaats(es.DocType):
    straatnaam = es.String(analyzer=analyzers.adres)
    adres = es.String(analyzer=analyzers.adres)

    huisnummer_variation = es.String(analyzer=analyzers.huisnummer)

    huisletter = es.String(analyzers=analyzers.toevoeging)
    huistoevoeging = es.String(analyzers=analyzers.toevoeging)

    huisnummer = es.Integer()

    postcode = es.String(analyzer=analyzers.postcode)
    order = es.Integer()

    centroid = es.GeoPoint()

    class Meta:
        index = settings.ELASTIC_INDICES['BAG']


class Standplaats(es.DocType):
    straatnaam = es.String(analyzer=analyzers.adres)
    adres = es.String(analyzer=analyzers.adres)

    huisnummer_variation = es.String(analyzer=analyzers.huisnummer)
    huisnummer = es.Integer()

    postcode = es.String(analyzer=analyzers.postcode)
    order = es.Integer()

    centroid = es.GeoPoint()

    class Meta:
        index = settings.ELASTIC_INDICES['BAG']


class Verblijfsobject(es.DocType):
    straatnaam = es.String(analyzer=analyzers.adres)
    adres = es.String(analyzer=analyzers.adres)
    huisnummer_variation = es.String(analyzer=analyzers.huisnummer)
    huisnummer = es.Integer()
    postcode = es.String(analyzer=analyzers.postcode)
    order = es.Integer()

    centroid = es.GeoPoint()

    bestemming = es.String()
    kamers = es.Integer()
    oppervlakte = es.Integer()

    class Meta:
        index = settings.ELASTIC_INDICES['BAG']


class OpenbareRuimte(es.DocType):
    naam = es.String(analyzer=analyzers.adres)
    postcode = es.String(analyzer=analyzers.postcode)
    order = es.Integer()

    subtype = es.String(analyzer=analyzers.subtype)

    class Meta:
        index = settings.ELASTIC_INDICES['BAG']


class Nummeraanduiding(es.DocType):
    """
    All BAG objects should have one or more adresses

    Een nummeraanduiding, in de volksmond ook wel adres genoemd, is een door
    het bevoegde gemeentelijke orgaan als
    zodanig toegekende aanduiding van een verblijfsobject, standplaats of
    ligplaats.

    [Stelselpedia](http://www.amsterdam.nl/stelselpedia/bag-index/catalogus-bag/objectklasse-2/)
    """
    straatnaam = es.String(analyzer=analyzers.adres)
    straatnaam_all = es.String(analyzer=analyzers.adres)
    # straatnaam_nen = es.String(analyzers=analyzers.adres)
    # straatnaam_ptt = es.String(analyzers=analyzers.adres)

    adres = es.String(analyzer=analyzers.adres)
    huisnummer_variation = es.String(analyzer=analyzers.huisnummer)
    huisnummer = es.Integer()
    huisnummer_str = es.String()
    toevoeging = es.String()
    toevoeging_variation = es.String(analyzer=analyzers.toevoeging)
    postcode = es.String(analyzer=analyzers.postcode)

    order = es.Integer()

    subtype = es.String(analyzer=analyzers.subtype)

    class Meta:
        index = settings.ELASTIC_INDICES['NUMMERAANDUIDING']


def get_centroid(geom):
    if not geom:
        return None

    result = geom.centroid
    result.transform('wgs84')
    return result.coords


def update_adres(dest, adres: models.Nummeraanduiding):
    if adres:
        dest.adres = adres.adres()
        dest.postcode = "{} {}".format(adres.postcode, adres.toevoeging)
        dest.straatnaam = adres.openbare_ruimte.naam

        dest.huisnummer = adres.huisnummer
        dest.huisnummer_variation = adres.huisnummer


def add_verblijfsobject(doc, vo: models.Verblijfsobject):
    if vo:
        doc.centroid = get_centroid(vo.geometrie)
        doc.subtype_id = vo.id
        doc.order = analyzers.orderings['adres']


def add_standplaats(doc, sp: models.Standplaats):
    if sp:
        doc.centroid = get_centroid(sp.geometrie)
        doc.subtype_id = sp.id
        doc.order = analyzers.orderings['adres']


def add_ligplaats(doc, lp: models.Ligplaats):
    if lp:
        doc.centroid = get_centroid(lp.geometrie)
        doc.subtype_id = lp.id
        doc.order = analyzers.orderings['adres']


def from_ligplaats(l: models.Ligplaats):
    # id unique
    d = Ligplaats(_id=l.id)

    update_adres(d, l.hoofdadres)

    d.centroid = get_centroid(l.geometrie)
    d.order = analyzers.orderings['adres']

    return d


def from_nummeraanduiding_ruimte(n: models.Nummeraanduiding):
    doc = Nummeraanduiding(_id=n.id)

    doc.adres = n.adres()

    doc.postcode = "{} {}".format(n.postcode, n.toevoeging)

    doc.straatnaam_all = "{} {} {}".format(
        n.openbare_ruimte.naam,
        n.openbare_ruimte.naam_nen,
        n.openbare_ruimte.naam_ptt,
        n.postcode,
    )

    # all variations of streets
    doc.straatnaam = n.openbare_ruimte.naam
    doc.straatnaam_nen = n.openbare_ruimte.naam_nen
    doc.straatnaam_ptt = n.openbare_ruimte.naam_ptt

    doc.huisnummer = n.huisnummer
    # we can use this one in matchers
    doc.huisnummer_str = n.huisnummer

    huisnummer_all = "{} {} {}".format(
        n.huisnummer,
        n.huisletter if n.huisletter else "",
        n.huisnummer_toevoeging if n.huisnummer_toevoeging else "")

    doc.huisletter = n.huisletter if n.huisletter else ""

    if n.huisnummer_toevoeging:
        doc.huistoevoeging = n.huisnummer_toevoeging

    # we use this field for ordering
    # doc.huisnummer_ord = ummer_all.replace(' ', '')

    # we use this field for searching
    doc.huisnummer_all = huisnummer_all

    doc.huisnummer_variation = n.huisnummer

    #
    # if n.buurt:
    #     d.buurt = n.buurt.naam

    # if n.stadsdeel:
    #     d.stadsdeel = n.stadsdeel.naam

    # if n.woonplaats:
    #     d.woonplaats = n.woonplaats.naam

    # if n.buurtcombinatie:
    #     d.buurtcombinatie = n.buurtcombinatie.naam

    if n.bron:
        doc.bron = n.bron.omschrijving

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

    return doc


def from_standplaats(s: models.Standplaats):

    d = Standplaats(_id=s.id)

    update_adres(d, s.hoofdadres)

    d.centroid = get_centroid(s.geometrie)
    d.order = analyzers.orderings['adres']

    return d


def from_verblijfsobject(v: models.Verblijfsobject):
    d = Verblijfsobject(_id=v.id)
    update_adres(d, v.hoofdadres)
    d.centroid = get_centroid(v.geometrie)

    d.bestemming = v.gebruiksdoel_omschrijving
    d.kamers = v.aantal_kamers
    d.oppervlakte = v.oppervlakte
    d.order = analyzers.orderings['adres']

    return d


def from_openbare_ruimte(o: models.OpenbareRuimte):
    d = OpenbareRuimte(_id=o.id)
    d.type = 'Openbare ruimte'
    d.subtype = o.get_type_display().lower()
    d.naam = o.naam
    postcodes = set()

    for a in o.adressen.all():
        if a.postcode:
            postcodes.add(a.postcode)

    d.postcode = list(postcodes)
    d.order = analyzers.orderings['openbare_ruimte']

    return d
