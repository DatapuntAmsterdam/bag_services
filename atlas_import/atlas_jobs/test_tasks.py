from django.test import TestCase

# Create your tests here.
from atlas_jobs import jobs
from atlas import models


BAG = 'atlas_jobs/fixtures/testset/bag'
GEBIEDEN = 'atlas_jobs/fixtures/testset/gebieden'


class ImportBrnTest(TestCase):
    def test_import(self):
        task = jobs.ImportBrnTask(BAG)
        task.execute()

        imported = models.Bron.objects.all()
        self.assertEqual(len(imported), 100)

        self.assertIsNotNone(models.Bron.objects.get(pk='PST'))

        b = models.Bron.objects.get(pk='13')
        self.assertEqual(b.omschrijving, 'Stadsdeel Zuideramstel (13)')

    def test_import_twice(self):
        task = jobs.ImportBrnTask(BAG)
        task.execute()
        task.execute()

        imported = models.Bron.objects.all()
        self.assertEqual(len(imported), 100)


class ImportStsTest(TestCase):
    def test_import(self):
        task = jobs.ImportStsTask(BAG)
        task.execute()

        imported = models.Status.objects.all()
        self.assertEqual(len(imported), 43)

        self.assertIsNotNone(models.Status.objects.get(pk='10'))

        s = models.Status.objects.get(pk='01')
        self.assertEqual(s.omschrijving, 'Buitengebruik i.v.m. renovatie')


class ImportGmeTest(TestCase):
    def test_import(self):
        task = jobs.ImportGmeTask(GEBIEDEN)
        task.execute()

        imported = models.Gemeente.objects.all()
        self.assertEqual(len(imported), 1)

        g = models.Gemeente.objects.get(pk='03630000000000')

        self.assertEquals(g.id, '03630000000000')
        self.assertEquals(g.code, '0363')
        self.assertEquals(g.naam, 'Amsterdam')
        self.assertTrue(g.verzorgingsgebied)
        self.assertFalse(g.vervallen)


class ImportSdlTest(TestCase):
    def test_import(self):
        jobs.ImportGmeTask(GEBIEDEN).execute()

        task = jobs.ImportSdlTask(GEBIEDEN)
        task.execute()

        imported = models.Stadsdeel.objects.all()
        self.assertEqual(len(imported), 8)

        s = models.Stadsdeel.objects.get(pk='03630011872037')

        self.assertEquals(s.id, '03630011872037')
        self.assertEquals(s.code, 'F')
        self.assertEquals(s.naam, 'Nieuw-West')
        self.assertEquals(s.vervallen, False)
        self.assertEquals(s.gemeente.id, '03630000000000')


class ImportBrtTest(TestCase):
    def test_import(self):
        jobs.ImportGmeTask(GEBIEDEN).execute()
        jobs.ImportSdlTask(GEBIEDEN).execute()

        task = jobs.ImportBrtTask(GEBIEDEN)
        task.execute()

        imported = models.Buurt.objects.all()
        self.assertEqual(len(imported), 481)

        b = models.Buurt.objects.get(pk='03630000000796')

        self.assertEquals(b.id, '03630000000796')
        self.assertEquals(b.code, '44b')
        self.assertEquals(b.naam, 'Westlandgrachtbuurt')
        self.assertEquals(b.vervallen, False)
        self.assertEquals(b.stadsdeel.id, '03630011872038')


class ImportLigTest(TestCase):
    def test_import(self):
        jobs.ImportBrnTask(BAG).execute()
        jobs.ImportStsTask(BAG).execute()

        jobs.ImportGmeTask(GEBIEDEN).execute()
        jobs.ImportSdlTask(GEBIEDEN).execute()
        jobs.ImportBrtTask(GEBIEDEN).execute()

        task = jobs.ImportLigTask(BAG)
        task.execute()

        imported = models.Ligplaats.objects.all()
        self.assertEqual(len(imported), 60)

        l = models.Ligplaats.objects.get(pk='03630001024868')
        self.assertEquals(l.identificatie, '03630001024868')
        self.assertEquals(l.vervallen, False)
        self.assertIsNone(l.bron)
        self.assertEquals(l.status.code, '33')
        self.assertEquals(l.buurt.id, '03630000000100')
