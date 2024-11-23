from django.test import TestCase

from pouet.models import Production


class TestModels(TestCase):
    fixtures = ['tests/pouet.json']

    def test_release_date(self):
        pondlife = Production.objects.get(name="Pondlife")
        self.assertEqual(str(pondlife.release_date), "March 2001")
