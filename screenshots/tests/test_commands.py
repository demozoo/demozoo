from __future__ import absolute_import, unicode_literals

import datetime

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from mock import patch

from mirror.models import ArchiveMember, Download
from productions.models import Production, ProductionType


class TestFetchRemoteScreenshots(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        skyrider = Production.objects.get(title="Skyrider")
        self.link = skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.scr',
            is_download_link=True
        )

    @patch('screenshots.management.commands.fetch_remote_screenshots.create_screenshot_from_production_link')
    def test_run(self, create_screenshot_from_production_link):

        with captured_stdout():
            call_command('fetch_remote_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 1)
        link_id, = create_screenshot_from_production_link.delay.call_args.args
        self.assertEqual(link_id, self.link.id)


class TestFetchRemoteZippedScreenshots(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.skyrider = Production.objects.get(title="Skyrider")

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_run_new(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 1)
        link_id, = create_screenshot_from_production_link.delay.call_args.args
        self.assertEqual(link_id, link.id)

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_ignore_non_zip(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.rar',
            is_download_link=True
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 0)

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_ignore_ascii(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="ASCII")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 0)

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_ignore_known_too_big(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True
        )
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 6, 1), error_type='FileTooBig'
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 0)

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_good_file_for_screenshot(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True, file_for_screenshot='skyrider.scr'
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 1)
        link_id, = create_screenshot_from_production_link.delay.call_args.args
        self.assertEqual(link_id, link.id)

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_bad_file_for_screenshot(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True, file_for_screenshot='skyrider.tap'
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 0)

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_select_archive_member(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True
        )
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 6, 1), sha1='012345678'
        )
        ArchiveMember.objects.create(
            archive_sha1='012345678', filename='skyrider.nfo', file_size=100
        )
        ArchiveMember.objects.create(
            archive_sha1='012345678', filename='skyrider.scr', file_size=6912
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 1)
        link_id, = create_screenshot_from_production_link.delay.call_args.args
        self.assertEqual(link_id, link.id)

        link.refresh_from_db()
        self.assertEqual(link.file_for_screenshot, 'skyrider.scr')

    @patch('screenshots.management.commands.fetch_remote_zipped_screenshots.create_screenshot_from_production_link')
    def test_unresolved_archive_member(self, create_screenshot_from_production_link):
        self.skyrider.types = [ProductionType.objects.get(name="Graphics")]
        link = self.skyrider.links.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            is_download_link=True
        )
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/skyrider.zip',
            downloaded_at=datetime.date(2020, 6, 1), sha1='012345678'
        )
        ArchiveMember.objects.create(
            archive_sha1='012345678', filename='skyrider.nfo', file_size=100
        )
        ArchiveMember.objects.create(
            archive_sha1='012345678', filename='skyrider.scr', file_size=6912
        )
        ArchiveMember.objects.create(
            archive_sha1='012345678', filename='skyrider-alt.scr', file_size=6912
        )

        with captured_stdout():
            call_command('fetch_remote_zipped_screenshots')

        self.assertEqual(create_screenshot_from_production_link.delay.call_count, 0)

        link.refresh_from_db()
        self.assertTrue(link.is_unresolved_for_screenshotting)
