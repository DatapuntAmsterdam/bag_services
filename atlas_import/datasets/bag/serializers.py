from rest_framework import serializers

from datasets.generic import rest
from . import models


class BagMixin(rest.DataSetSerializerMixin):
    dataset = 'bag'


class Status(serializers.ModelSerializer):
    class Meta:
        model = models.Status
        fields = ('code', 'omschrijving')


class Eigendomsverhouding(serializers.ModelSerializer):
    class Meta:
        model = models.Eigendomsverhouding
        fields = ('code', 'omschrijving')


class Financieringswijze(serializers.ModelSerializer):
    class Meta:
        model = models.Financieringswijze
        fields = ('code', 'omschrijving')


class Gebruik(serializers.ModelSerializer):
    class Meta:
        model = models.Gebruik
        fields = ('code', 'omschrijving')


class Ligging(serializers.ModelSerializer):
    class Meta:
        model = models.Ligging
        fields = ('code', 'omschrijving')


class LocatieIngang(serializers.ModelSerializer):
    class Meta:
        model = models.LocatieIngang
        fields = ('code', 'omschrijving')


class Toegang(serializers.ModelSerializer):
    class Meta:
        model = models.Toegang
        fields = ('code', 'omschrijving')


class Woonplaats(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Woonplaats
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )


class WoonplaatsDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    openbare_ruimtes = rest.RelatedSummaryField()

    class Meta:
        model = models.Woonplaats
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'begin_geldigheid',
            'einde_geldigheid',
            'mutatie_gebruiker',

            'naam',
            'naam_ptt',
            'gemeente',
            'openbare_ruimtes'
        )


class OpenbareRuimte(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.OpenbareRuimte
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )


class OpenbareRuimteDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    status = Status()
    type = serializers.CharField(source='get_type_display')
    adressen = rest.RelatedSummaryField()
    woonplaats = Woonplaats()

    class Meta:
        model = models.OpenbareRuimte
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'code',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'begin_geldigheid',
            'einde_geldigheid',
            'mutatie_gebruiker',
            'status',
            'bron',

            'type',
            'naam',
            'naam_ptt',
            'naam_nen',
            'straat_nummer',
            'woonplaats',
            'adressen',
        )


class Ligplaats(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Ligplaats
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )

    def display(self, obj):
        return obj.hoofdadres.adres()


class LigplaatsDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    status = Status()
    hoofdadres = serializers.HyperlinkedRelatedField(
        source='hoofdadres.id',
        view_name='nummeraanduiding-detail',
        read_only=True,
    )
    adressen = rest.RelatedSummaryField()

    class Meta:
        model = models.Ligplaats
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'begin_geldigheid',
            'einde_geldigheid',
            'mutatie_gebruiker',
            'status',
            'bron',

            'geometrie',
            'hoofdadres',
            'adressen',
            'buurt',
        )


class Nummeraanduiding(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Nummeraanduiding
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )


class NummeraanduidingDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    status = Status()
    type = serializers.CharField(source='get_type_display')

    class Meta:
        model = models.Nummeraanduiding
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'begin_geldigheid',
            'einde_geldigheid',
            'mutatie_gebruiker',
            'status',
            'bron',
            'adres',

            'postcode',
            'huisnummer',
            'huisletter',
            'huisnummer_toevoeging',
            'type',
            'adres_nummer',
            'openbare_ruimte',
            'hoofdadres',
            'ligplaats',
            'standplaats',
            'verblijfsobject',
        )


class Standplaats(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Standplaats
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )


class StandplaatsDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    status = Status()
    adressen = rest.RelatedSummaryField()
    hoofdadres = serializers.HyperlinkedRelatedField(
        source='hoofdadres.id',
        view_name='nummeraanduiding-detail',
        read_only=True,
    )

    class Meta:
        model = models.Standplaats
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'begin_geldigheid',
            'einde_geldigheid',
            'mutatie_gebruiker',
            'status',
            'bron',

            'geometrie',
            'hoofdadres',
            'adressen',
            'buurt',
        )


class KadastraalObjectField(serializers.HyperlinkedRelatedField):
    view_name = "kadastraalobject-detail"


class Verblijfsobject(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Verblijfsobject
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )


class VerblijfsobjectDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    status = Status()
    eigendomsverhouding = Eigendomsverhouding()
    financieringswijze = Financieringswijze()
    gebruik = Gebruik()
    ligging = Ligging()
    locatie_ingang = LocatieIngang()
    toegang = Toegang()
    status_coordinaat = serializers.SerializerMethodField()
    type_woonobject = serializers.SerializerMethodField()
    gebruiksdoel = serializers.SerializerMethodField()
    hoofdadres = serializers.HyperlinkedRelatedField(
        source='hoofdadres.id',
        view_name='nummeraanduiding-detail',
        read_only=True,
    )
    kadastrale_objecten = rest.RelatedSummaryField()
    panden = rest.RelatedSummaryField()
    adressen = rest.RelatedSummaryField()

    class Meta:
        model = models.Verblijfsobject
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'begin_geldigheid',
            'einde_geldigheid',
            'mutatie_gebruiker',
            'status',
            'bron',

            'geometrie',
            'gebruiksdoel',
            'oppervlakte',
            'bouwlaag_toegang',
            'status_coordinaat',
            'verhuurbare_eenheden',
            'bouwlagen',
            'type_woonobject',
            'woningvoorraad',
            'aantal_kamers',
            'reden_afvoer',
            'eigendomsverhouding',
            'financieringswijze',
            'gebruik',
            'ligging',
            'locatie_ingang',
            'toegang',
            'hoofdadres',
            'adressen',
            'buurt',
            'panden',
            'kadastrale_objecten',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        expand = 'full' in self.context['request'].query_params

        if expand:
            self.fields['adressen'] = serializers.ManyRelatedField(child_relation=Nummeraanduiding())
            self.fields['panden'] = serializers.ManyRelatedField(child_relation=Pand())

    def get_gebruiksdoel(self, obj):
        return dict(
            code=obj.gebruiksdoel_code,
            omschrijving=obj.gebruiksdoel_omschrijving,
        )

    def get_status_coordinaat(self, obj):
        return dict(
            code=obj.status_coordinaat_code,
            omschrijving=obj.status_coordinaat_omschrijving,
        )

    def get_type_woonobject(self, obj):
        return dict(
            code=obj.type_woonobject_code,
            omschrijving=obj.type_woonobject_omschrijving,
        )


class Pand(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Pand
        fields = (
            '_links',
            '_display',
            'landelijk_id',
        )


class PandDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    status = Status()
    verblijfsobjecten = rest.RelatedSummaryField()

    class Meta:
        model = models.Pand
        fields = (
            '_links',
            '_display',
            'id',
            'landelijk_id',
            'date_modified',
            'document_mutatie',
            'document_nummer',
            'status',

            'geometrie',

            'bouwjaar',
            'hoogste_bouwlaag',
            'laagste_bouwlaag',
            'pandnummer',

            'verblijfsobjecten',
            'bouwblok',
        )


class Gemeente(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Gemeente
        fields = (
            '_links',
            '_display',
            'code',
        )


class GemeenteDetail(BagMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    woonplaatsen = rest.RelatedSummaryField()

    class Meta:
        model = models.Gemeente
        fields = (
            '_links',
            '_display',
            'id',
            'code',
            'date_modified',

            'naam',
            'verzorgingsgebied',
            'woonplaatsen',
        )


class GebiedenMixin(rest.DataSetSerializerMixin):
    dataset = 'gebieden'


class Stadsdeel(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Stadsdeel
        fields = (
            '_links',
            '_display',
            'code',
            'naam',
        )


class StadsdeelDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    buurten = rest.RelatedSummaryField()
    gebiedsgerichtwerken = rest.RelatedSummaryField()

    class Meta:
        model = models.Stadsdeel
        fields = (
            '_links',
            '_display',
            'id',
            'code',
            'date_modified',

            'naam',
            'gemeente',
            'ingang_cyclus',
            'brondocument_naam',
            'brondocument_datum',
            'geometrie',
            'buurten',
            'gebiedsgerichtwerken',
        )


class Buurt(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Buurt
        fields = (
            '_links',
            '_display',
            'code',
        )


class BuurtDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    bouwblokken = rest.RelatedSummaryField()
    ligplaatsen = rest.RelatedSummaryField()
    standplaatsen = rest.RelatedSummaryField()
    verblijfsobjecten = rest.RelatedSummaryField()

    class Meta:
        model = models.Buurt
        fields = (
            '_links',
            '_display',
            'code',

            'naam',
            'stadsdeel',
            'ingang_cyclus',
            'brondocument_naam',
            'brondocument_datum',
            'geometrie',
            'bouwblokken',
            'ligplaatsen',
            'standplaatsen',
            'verblijfsobjecten',
        )


class Bouwblok(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Bouwblok
        fields = (
            '_links',
            '_display',
            'code',
        )


class BouwblokDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()
    panden = rest.RelatedSummaryField()

    class Meta:
        model = models.Bouwblok
        fields = (
            '_links',
            '_display',
            'code',
            'buurt',
            'ingang_cyclus',
            'geometrie',
            'panden',
        )


class Buurtcombinatie(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Buurtcombinatie
        fields = (
            '_links',
            '_display',
            'naam',
        )


class BuurtcombinatieDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Buurtcombinatie
        fields = (
            '_links',
            '_display',
            'naam',
            'code',
            'vollcode',
            'brondocument_naam',
            'brondocument_datum',
            'ingang_cyclus',
            'geometrie',
        )


class Gebiedsgerichtwerken(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Gebiedsgerichtwerken
        fields = (
            '_links',
            '_display',
            'naam',
        )


class GebiedsgerichtwerkenDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Gebiedsgerichtwerken
        fields = (
            '_links',
            '_display',
            'naam',
            'code',
            'stadsdeel',
            'geometrie',
        )


class Grootstedelijkgebied(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Grootstedelijkgebied
        fields = (
            '_links',
            '_display',
            'naam',
        )


class GrootstedelijkgebiedDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Grootstedelijkgebied
        fields = (
            '_links',
            '_display',
            'naam',
            'geometrie',
        )


class Unesco(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Unesco
        fields = (
            '_links',
            '_display',
            'naam',
        )


class UnescoDetail(GebiedenMixin, rest.HALSerializer):
    _display = rest.DisplayField()

    class Meta:
        model = models.Unesco
        fields = (
            '_links',
            '_display',
            'naam',
            'geometrie',
        )
