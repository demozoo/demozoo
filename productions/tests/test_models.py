# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase
from freezegun import freeze_time
from mock import patch

from demoscene.models import Nick
from mirror.models import Download
from platforms.models import Platform
from productions.models import (
    Byline, Credit, PackMember, Production, ProductionLink, ProductionType, Screenshot
)


class TestProductionType(TestCase):
    fixtures = ['tests/gasman.json']

    def test_music_types(self):
        ProductionType.objects.filter(internal_name='music').delete()
        self.assertEqual(ProductionType.music_types().count(), 0)

    def test_graphic_types(self):
        ProductionType.objects.filter(internal_name='graphics').delete()
        self.assertEqual(ProductionType.graphic_types().count(), 0)


class TestProduction(TestCase):
    fixtures = ['tests/gasman.json']

    def test_title_with_byline(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.author_nicks.clear()
        pondlife.author_affiliation_nicks.clear()
        self.assertEqual(pondlife.title_with_byline, 'Pondlife')

    def test_multiple_platform_name(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.platforms.add(Platform.objects.get(name='Commodore 64'))
        self.assertEqual(pondlife.platform_name, '(multiple)')

    def test_multiple_type_name(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.types.add(ProductionType.objects.get(name='Intro'))
        self.assertEqual(pondlife.type_name, '(multiple)')


@freeze_time('2020-08-05')
class TestProductionLink(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.skyrider = Production.objects.get(title="Skyrider")
        self.link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True
        )

    def test_no_extension(self):
        extensionless_link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider',
            is_download_link=True
        )
        self.assertEqual(extensionless_link.download_file_extension(), None)
        self.assertFalse(extensionless_link.is_zip_file())

    @patch('productions.tasks.fetch_production_link_embed_data')
    def test_is_streaming_video(self, fetch_production_link_embed_data):
        self.assertFalse(self.link.is_streaming_video)

        video_link = self.skyrider.links.create(
            link_class='YoutubeVideo', parameter='ldoVS0idTBw',
            is_download_link=False
        )
        video_link = ProductionLink.objects.get(id=video_link.id)
        self.assertTrue(video_link.is_streaming_video)
        fetch_production_link_embed_data.delay.assert_called_once_with(video_link.id)

    def test_mirrored_file_believed_downloadable(self):
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 6, 1), mirror_s3_key='00/00/00000000.zip'
        )
        self.assertTrue(self.link.is_believed_downloadable())

    def test_unseen_file_believed_downloadable(self):
        self.assertTrue(self.link.is_believed_downloadable())

    def test_oversized_file_not_believed_downloadable(self):
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 6, 1), error_type='FileTooBig'
        )
        self.assertFalse(self.link.is_believed_downloadable())

    def test_recently_errored_file_not_believed_downloadable(self):
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 8, 1), error_type='HTTPError'
        )
        self.assertFalse(self.link.is_believed_downloadable())

    def test_older_errored_file_believed_downloadable(self):
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 6, 1), error_type='HTTPError'
        )
        self.assertTrue(self.link.is_believed_downloadable())


class TestByline(TestCase):
    fixtures = ['tests/gasman.json']

    def test_commit(self):
        prod = Production.objects.create(title="Tim Will Rock You", supertype="music")
        byline = Byline([Nick.objects.get(name='Gasman')], [Nick.objects.get(name='Hooy-Program')])
        byline.commit(prod)
        self.assertTrue(prod.author_nicks.filter(name='Gasman').exists())
        self.assertTrue(prod.author_affiliation_nicks.filter(name='Hooy-Program').exists())


class TestCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        pondlife = Production.objects.get(title='Pondlife')
        credit = pondlife.credits.get(nick__name='Gasman')
        self.assertEqual(str(credit), "Pondlife: Gasman - Code")
        credit.role='Part 1'
        self.assertEqual(str(credit), "Pondlife: Gasman - Code (Part 1)")


class TestScreenshot(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        pondlife = Production.objects.get(title='Pondlife')
        screenshot = Screenshot(production=pondlife, original_url='http://example.com/pondlife.png')
        self.assertEqual(str(screenshot), "Pondlife - http://example.com/pondlife.png")


class TestSoundtrackLink(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        pondlife = Production.objects.get(title='Pondlife')
        soundtrack = pondlife.soundtrack_links.get(soundtrack__title__startswith="Cyber")
        self.assertEqual(str(soundtrack), "Cybernoid's Revenge on Pondlife")


class TestPackMember(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.types.add(ProductionType.objects.get(name='Pack'))
        madrielle = Production.objects.get(title='Madrielle')
        pack_member = PackMember(pack=pondlife, member=madrielle, position=1)
        self.assertEqual(str(pack_member), "Madrielle packed in Pondlife")
