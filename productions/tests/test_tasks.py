from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase
from django.test.utils import captured_stdout
from freezegun import freeze_time

from productions.models import Production, ProductionLink
from productions.tasks import clean_dead_youtube_link, fetch_production_link_embed_data


class TestTasks(TestCase):
    fixtures = ['tests/gasman.json']

    def test_fetch_production_link_embed_data_non_existent(self):
        pondlife = Production.objects.get(title='Pondlife')

        # non-existent link
        fetch_production_link_embed_data(9999)

    @freeze_time('2020-10-01')
    def test_fetch_production_link_embed_data_fetched_last_month(self):
        pondlife = Production.objects.get(title='Pondlife')
        # create with a bogus link_class to prevent fetch_production_link_embed_data
        # from being called on save()
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='ldoVS0idTBw', is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(
            link_class='YoutubeVideo', embed_data_last_fetch_time=datetime.datetime(2020, 9, 20)
        )
        fetch_production_link_embed_data(link.id)
        link.refresh_from_db()
        self.assertEqual(link.embed_data_last_fetch_time, datetime.datetime(2020, 9, 20))
        self.assertEqual(link.embed_data_last_error_time, None)

    @freeze_time('2020-10-01')
    def test_fetch_production_link_embed_data_errored_last_month(self):
        pondlife = Production.objects.get(title='Pondlife')
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='ldoVS0idTBw', is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(
            link_class='YoutubeVideo', embed_data_last_error_time=datetime.datetime(2020, 9, 20)
        )
        fetch_production_link_embed_data(link.id)
        link.refresh_from_db()
        self.assertEqual(link.embed_data_last_error_time, datetime.datetime(2020, 9, 20))
        self.assertEqual(link.embed_data_last_fetch_time, None)

    def test_fetch_production_link_embed_data(self):
        pondlife = Production.objects.get(title='Pondlife')
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='ldoVS0idTBw', is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(
            link_class='YoutubeVideo'
        )
        fetch_production_link_embed_data(link.id)
        link.refresh_from_db()
        self.assertEqual(link.video_width, 1280)

    def test_fetch_production_link_embed_data_error(self):
        pondlife = Production.objects.get(title='Pondlife')
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='404', is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(
            link_class='YoutubeVideo'
        )
        fetch_production_link_embed_data(link.id)
        link.refresh_from_db()
        self.assertTrue(link.embed_data_last_error_time)

    def test_clean_dead_youtube_link_non_existent(self):
        pondlife = Production.objects.get(title='Pondlife')

        # non-existent link
        clean_dead_youtube_link(9999)

    def test_clean_dead_youtube_link(self):
        pondlife = Production.objects.get(title='Pondlife')
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='404', is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(
            link_class='YoutubeVideo'
        )
        with captured_stdout():
            clean_dead_youtube_link(link.id)
        self.assertEqual(pondlife.links.filter(link_class='YoutubeVideo').count(), 0)

    def test_keep_active_youtube_link(self):
        pondlife = Production.objects.get(title='Pondlife')
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='ldoVS0idTBw', is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(
            link_class='YoutubeVideo'
        )
        clean_dead_youtube_link(link.id)
        self.assertEqual(pondlife.links.filter(link_class='YoutubeVideo').count(), 1)
