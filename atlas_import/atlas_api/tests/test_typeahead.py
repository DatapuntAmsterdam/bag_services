from rest_framework.test import APITestCase
import time
import datasets.bag.batch
import datasets.akr.batch
from batch import batch

from datasets.bag.tests import factories as bag_factories


class TypeaheadTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        openbare_ruimte = bag_factories.OpenbareRuimteFactory.create(naam="Anjeliersstraat")
        bag_factories.NummeraanduidingFactory.create(openbare_ruimte=openbare_ruimte, huisnummer=11, huisletter='A',
                                                     hoofdadres=True)
        bag_factories.NummeraanduidingFactory.create(openbare_ruimte=openbare_ruimte, huisnummer=11, huisletter='B',
                                                     hoofdadres=True)
        bag_factories.NummeraanduidingFactory.create(openbare_ruimte=openbare_ruimte, huisnummer=11, huisletter='C',
                                                     hoofdadres=True)
        bag_factories.NummeraanduidingFactory.create(openbare_ruimte=openbare_ruimte, huisnummer=12, hoofdadres=True)

        openbare_ruimte = bag_factories.OpenbareRuimteFactory.create(naam="Marnixkade")
        bag_factories.NummeraanduidingFactory.create(openbare_ruimte=openbare_ruimte, huisnummer=36, huisletter='F',
                                                     hoofdadres=True, postcode='1051XR')

        batch.execute(datasets.bag.batch.IndexJob())
        batch.execute(datasets.akr.batch.IndexKadasterJob())
        time.sleep(1)   # this is stupid

    def test_match_openbare_ruimte(self):
        response = self.client.get('/api/atlas/typeahead/', dict(q="an"))
        self.assertEqual(response.status_code, 200)

        lst = response.data
        self.assertEqual(lst[0], dict(item="Anjeliersstraat"))

    def test_match_openbare_ruimte_lowercase(self):
        response = self.client.get('/api/atlas/typeahead/', dict(q="AN"))
        self.assertEqual(response.status_code, 200)

        lst = response.data
        self.assertEqual(lst[0], dict(item="Anjeliersstraat"))

    def test_match_maximum_length(self):
        response = self.client.get('/api/atlas/typeahead/', dict(q="a"))
        self.assertEqual(response.status_code, 200)

        lst = response.data
        self.assertEqual(len(lst), 5)

    def test_match_adresseerbaar_object(self):
        response = self.client.get('/api/atlas/typeahead/', dict(q="anjelier"))
        self.assertEqual(response.status_code, 200)

        lst = response.data
        self.assertEqual(lst[0], dict(item="Anjeliersstraat"))
        self.assertIn("Anjeliersstraat 11A", [l['item'] for l in lst])

    def test_match_adresseerbaar_object_met_huisnummer(self):
        response = self.client.get('/api/atlas/typeahead/', dict(q="anjeliersstraat 11"))
        lst = response.data
        self.assertTrue(lst[0]['item'].startswith("Anjeliersstraat 11"))

    def test_match_postcode(self):
        response = self.client.get("/api/atlas/typeahead/", dict(q='105'))
        lst = response.data
        self.assertTrue(lst[0]['item'].startswith('105'))



