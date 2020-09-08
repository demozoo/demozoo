# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase
from freezegun import freeze_time

from mirror.models import Download
from platforms.models import Platform
from productions.models import Production, ProductionType


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
