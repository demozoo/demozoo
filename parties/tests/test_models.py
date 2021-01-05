# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase
from freezegun import freeze_time

from fuzzy_date import FuzzyDate
from parties.models import Organiser, Party, PartySeries
from productions.models import Production
from sceneorg.models import Directory, File


class TestPartySeries(TestCase):
    fixtures = ['tests/gasman.json']

    def test_string(self):
        partyseries = PartySeries.objects.get(name="Forever")
        self.assertEqual(str(partyseries), "Forever")

    def test_plaintext_notes(self):
        partyseries = PartySeries.objects.get(name="Forever")
        partyseries.notes = "doo doo <i>doo</i> do do doo"
        partyseries.save()

        self.assertEqual(partyseries.plaintext_notes, "doo doo doo do do doo")


class TestParty(TestCase):
    fixtures = ['tests/gasman.json']

    def test_suffix(self):
        isp_series = PartySeries.objects.create(name="International Salmiakki Party")
        isp_party = isp_series.parties.create(
            name="International Salmiakki Party",
            start_date_date=datetime.date(2010, 6, 1),
            start_date_precision='d',
            end_date_date=datetime.date(2010, 6, 3),
            end_date_precision='d',
        )
        self.assertEqual(isp_party.suffix, 2010)

    @freeze_time('2020-05-15')
    def test_default_competition_date(self):
        forever = PartySeries.objects.get(name="Forever")

        forever_longparty = forever.parties.create(
            name="Forever Longparty 2020",
            start_date_date=datetime.date(2020, 5, 14),
            start_date_precision='d',
            end_date_date=datetime.date(2020, 5, 20),
            end_date_precision='d',
        )
        self.assertEqual(
            forever_longparty.default_competition_date(),
            FuzzyDate(datetime.date(2020, 5, 15), 'd')
        )

        forever_futureparty = forever.parties.create(
            name="Forever Futureparty 2020",
            start_date_date=datetime.date(2020, 5, 17),
            start_date_precision='d',
            end_date_date=datetime.date(2020, 5, 20),
            end_date_precision='d',
        )
        self.assertEqual(
            forever_futureparty.default_competition_date(),
            FuzzyDate(datetime.date(2020, 5, 17), 'd')
        )

        forever_fuzzyparty = forever.parties.create(
            name="Forever Fuzzyparty 2020",
            start_date_date=datetime.date(2020, 3, 1),
            start_date_precision='m',
            end_date_date=datetime.date(2020, 3, 1),
            end_date_precision='m',
        )
        self.assertEqual(
            forever_fuzzyparty.default_competition_date(),
            FuzzyDate(datetime.date(2020, 3, 1), 'm')
        )

    def test_sceneorg_results_file(self):
        forever = Party.objects.get(name="Forever 2e3")
        forever.external_links.create(
            link_class='SceneOrgFolder',
            parameter='/parties/2000/forever00/'
        )
        sceneorg_dir = Directory.objects.create(
            path='/parties/2000/forever00/',
            last_seen_at=datetime.datetime.now(),
        )
        results = File.objects.create(
            path='/parties/2000/forever00/results.txt',
            last_seen_at=datetime.datetime.now(),
            directory=sceneorg_dir
        )
        self.assertEqual(forever.sceneorg_results_file(), results)
        forever.add_sceneorg_file_as_results_file(results)
        self.assertEqual(forever.results_files.count(), 1)

    def test_share_image_url(self):
        forever = Party.objects.get(name="Forever 2e3")

        pondlife = Production.objects.get(title='Pondlife')
        screenshot = pondlife.screenshots.create(
            thumbnail_url='http://example.com/pondlife.thumb.png', thumbnail_width=130, thumbnail_height=100,
            standard_url='http://example.com/pondlife.standard.png', standard_width=400, standard_height=300,
        )
        forever.share_screenshot = screenshot
        forever.save()

        self.assertEqual(forever.share_image_url, 'http://example.com/pondlife.standard.png')


class TestCompetitionPlacing(TestCase):
    fixtures = ['tests/gasman.json']

    def test_string(self):
        placing = Production.objects.get(title="Madrielle").competition_placings.first()
        self.assertEqual(str(placing), "Madrielle")


class TestOrganiser(TestCase):
    fixtures = ['tests/gasman.json']

    def test_string(self):
        orga = Party.objects.get(name="Revision 2011").organisers.get(releaser__name="Gasman")
        self.assertEqual(str(orga), "Gasman - Compo team at Revision 2011")
