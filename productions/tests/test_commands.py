from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.test.utils import captured_stdout
from mock import patch

from productions.models import Production, ProductionLink


class TestFetchEmbedData(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('productions.tasks.fetch_production_link_embed_data')
    def test_run(self, fetch_production_link_embed_data):
        pondlife = Production.objects.get(title='Pondlife')
        # create with a bogus link_class to prevent fetch_production_link_embed_data
        # from being called on save()
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='1lFBXWxSrKE',
            is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(link_class='YoutubeVideo')

        with captured_stdout():
            call_command('fetch_embed_data')

        fetch_production_link_embed_data.delay.assert_called_once_with(link.id)
