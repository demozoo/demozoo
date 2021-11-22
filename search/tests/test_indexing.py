from django.core.management import call_command
from django.test import TestCase

from demoscene.models import Releaser


class TestIndexing(TestCase):
    fixtures = ['tests/gasman.json']

    def test_index(self):
        call_command('reindex')

        gasman = Releaser.objects.get(name="Gasman")
        self.assertTrue(gasman.search_document)
