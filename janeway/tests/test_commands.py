from __future__ import absolute_import, unicode_literals

import datetime

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from mock import patch

from productions.models import Production


class TestFillJanewayReleaseDates(TestCase):
    fixtures = ['tests/janeway.json']

    def test_run(self):
        sota = Production.objects.create(
            title="State Of The Art", supertype="production"
        )
        sota.links.create(link_class='KestraBitworldRelease', parameter=345)
        with captured_stdout():
            call_command('fill_janeway_release_dates')

        self.assertEqual(
            Production.objects.get(pk=sota.pk).release_date_date,
            datetime.date(1992, 12, 29)
        )


class TestImportJanewayScreenshots(TestCase):
    fixtures = ['tests/janeway.json']

    @patch('janeway.tasks.import_screenshot')
    def test_run(self, import_screenshot):
        sota = Production.objects.create(
            title="State Of The Art", supertype="production"
        )
        sota.links.create(link_class='KestraBitworldRelease', parameter=345)
        with captured_stdout():
            call_command('import_janeway_screenshots')

        self.assertEqual(import_screenshot.delay.call_count, 1)
        production_id, screenshot_janeway_id, screenshot_url, screenshot_suffix = import_screenshot.delay.call_args.args
        self.assertEqual(production_id, sota.id)
        self.assertEqual(screenshot_janeway_id, 111)
        self.assertEqual(screenshot_url, "http://kestra.exotica.org.uk/files/screenies/28000/154a.png")
        self.assertEqual(screenshot_suffix, "a")
