from __future__ import absolute_import, unicode_literals

import datetime

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

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
