import gzip
import json

import responses
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from freezegun import freeze_time

from demoscene.models import Releaser
from pouet.models import CompetitionType, Group, GroupMatchInfo, Party
from pouet.models import Production as PouetProduction
from productions.models import Production, ProductionType


TBL = {
    "id": "1",
    "name": "The Black Lotus",
    "acronym": "TBL",
    "disambiguation": "",
    "web": "https://archive.is/20130113112736/http://www.tbl.org",
    "addedUser": "1",
    "addedDate": "2000-04-23 10:41:05",
    "csdb": "0",
    "zxdemo": "0",
    "demozoo": "9"
}


ASTRAL_BLUR = {
    "id": "1",
    "name": "Astral Blur",
    "download": "https://files.scene.org/view/demos/groups/tbl/pc/astral.zip",
    "types": ["demo"],
    "platforms": {
        "67": {"name": "MS-Dos", "icon": "k_msdos.gif", "slug": "msdos"},
    },
    "placings": [
        {
            "party": {"id": "43", "name": "The Gathering", "web": "http://www.gathering.org/"},
            "compo": "95", "ranking": "3", "year": "1997", "compo_name": "pc demo"
        },
    ],
    "groups": [
        {
            "id": "1", "name": "The Black Lotus", "acronym": "TBL",
            "disambiguation": "", "web": "https://archive.is/20130113112736/http://www.tbl.org",
            "addedUser": "1", "addedDate": "2000-04-23 10:41:05"
        }
    ],
    "awards": [],
    "type": "demo",
    "addedUser": "1",
    "addedDate": "2000-04-23 10:44:48",
    "releaseDate": "1997-03-15",
    "voteup":"80",
    "votepig":"18",
    "votedown":"5",
    "voteavg":"0.73",
    "party_compo": "95",
    "party_place": "3",
    "party_year": "1997",
    "party": {"id": "43", "name": "The Gathering", "web": "http://www.gathering.org/"},
    "addeduser": {
        "id": "1", "nickname": "analogue", "level": "administrator", "avatar": "bobble.gif",
        "glops": "850", "registerDate": "2000-06-25 17:59:58"
    },
    "sceneorg": "0",
    "demozoo": "11",
    "csdb": "0",
    "zxdemo": "0",
    "invitation": None,
    "invitationyear": "2000",
    "boardID": None,
    "rank": "665",
    "cdc": 0,
    "downloadLinks": [
        {"type": "youtube", "link": "https://www.youtube.com/watch?v=eZyLSHyUGBY"}
    ],
    "credits": [
        {
            "user": {
                "id": "1199", "nickname": "Jace_TBL", "level": "user", "avatar": "taikyoku.gif",
                "glops": "40", "registerDate": "2001-09-25 01:48:39"
            },
            "role": "Code (additional)"
        },
    ],
    "popularity": 72.255773153818,
    "screenshot": "http://content.pouet.net/files/screenshots/00000/00000001.jpg",
    "party_compo_name": "pc demo"
}


@freeze_time('2021-11-01')
class TestFetchPouetData(TestCase):
    def add_groups_response(self):
        group_json = json.dumps({
            "dump_date": "2021-10-27 04:30:01",
            "groups": [
                TBL,
            ]
        })
        group_gzdata = gzip.compress(group_json.encode('utf-8'))
        responses.add(
            responses.GET, 'https://data.pouet.net/dumps/202110/pouetdatadump-groups-20211027.json.gz',
            body=group_gzdata
        )

    def add_prods_response(self, prod):
        prod_json = json.dumps({
            "dump_date": "2021-10-27 04:30:01",
            "prods": [
                prod,
            ]
        })
        prod_gzdata = gzip.compress(prod_json.encode('utf-8'))
        responses.add(
            responses.GET, 'https://data.pouet.net/dumps/202110/pouetdatadump-prods-20211027.json.gz',
            body=prod_gzdata
        )

    @responses.activate
    def test_run(self):
        self.add_groups_response()
        self.add_prods_response(ASTRAL_BLUR)

        tbl = Releaser.objects.create(name="The Black Lotus", is_group=True)
        tbl.external_links.create(link_class='PouetGroup', parameter='1')
        astral_blur = Production.objects.create(title="Astral Blur")
        astral_blur.author_nicks.add(tbl.primary_nick)
        astral_blur.types.add(ProductionType.objects.get(name='Demo'))

        # create a group with no Pouet link and a stale GroupMatchInfo record
        spacepigs = Releaser.objects.create(name="Spacepigs", is_group=True)
        GroupMatchInfo.objects.create(
            releaser=spacepigs,
            matched_production_count=1,
            unmatched_demozoo_production_count=1,
            unmatched_pouet_production_count=1
        )

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet = PouetProduction.objects.get(name="Astral Blur")
        self.assertEqual(
            astral_blur_pouet.groups.first(),
            Group.objects.get(name="The Black Lotus")
        )
        self.assertEqual(
            astral_blur.links.get(link_class='PouetProduction').parameter, '1'
        )
        self.assertEqual(
            astral_blur_pouet.download_links.get().url,
            "https://www.youtube.com/watch?v=eZyLSHyUGBY"
        )
        self.assertEqual(str(astral_blur_pouet.release_date), "March 1997")

        astral_blur_pouet.download_links.create(
            url="http://example.com/astralblur.mp4", link_type="video"
        )

        # re-run to confirm that existing records are handled correctly
        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet_new = PouetProduction.objects.get(name="Astral Blur")
        self.assertEqual(astral_blur_pouet_new.id, astral_blur_pouet.id)

        # extra link should have been deleted
        self.assertEqual(
            astral_blur_pouet.download_links.get().url,
            "https://www.youtube.com/watch?v=eZyLSHyUGBY"
        )

        # GroupMatchInfo record for spacepigs should have been garbage-collected
        self.assertFalse(GroupMatchInfo.objects.filter(releaser=spacepigs).exists())
        # but one for tbl should have been created
        self.assertTrue(GroupMatchInfo.objects.filter(releaser=tbl).exists())

    @responses.activate
    def test_run_with_release_date_year(self):
        self.add_groups_response()

        ASTRAL_BLUR_1997 = ASTRAL_BLUR.copy()
        ASTRAL_BLUR_1997['releaseDate'] = "1997-00-15"
        self.add_prods_response(ASTRAL_BLUR_1997)

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet = PouetProduction.objects.get(name="Astral Blur")
        self.assertEqual(str(astral_blur_pouet.release_date), "1997")

    @responses.activate
    def test_run_with_blank_release_date(self):
        self.add_groups_response()

        ASTRAL_BLUR_UNDATED = ASTRAL_BLUR.copy()
        ASTRAL_BLUR_UNDATED['releaseDate'] = None
        self.add_prods_response(ASTRAL_BLUR_UNDATED)

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet = PouetProduction.objects.get(name="Astral Blur")
        self.assertIsNone(astral_blur_pouet.release_date)

    @responses.activate
    def test_run_with_null_year_in_placing_data(self):
        self.add_groups_response()

        ASTRAL_BLUR_BAD_PLACING = ASTRAL_BLUR.copy()
        BAD_PLACING = ASTRAL_BLUR['placings'][0].copy()
        BAD_PLACING['year'] = None
        ASTRAL_BLUR_BAD_PLACING['placings'] = [BAD_PLACING]
        self.add_prods_response(ASTRAL_BLUR_BAD_PLACING)

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet = PouetProduction.objects.get(name="Astral Blur")
        self.assertEqual(astral_blur_pouet.competition_placings.count(), 0)

    @responses.activate
    def test_run_with_null_compo_in_placing_data(self):
        self.add_groups_response()

        ASTRAL_BLUR_BAD_PLACING = ASTRAL_BLUR.copy()
        BAD_PLACING = ASTRAL_BLUR['placings'][0].copy()
        BAD_PLACING['compo'] = None
        ASTRAL_BLUR_BAD_PLACING['placings'] = [BAD_PLACING]
        self.add_prods_response(ASTRAL_BLUR_BAD_PLACING)

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet = PouetProduction.objects.get(name="Astral Blur")
        self.assertIsNone(
            astral_blur_pouet.competition_placings.first().competition_type
        )

    @responses.activate
    def test_nullify_ranking_in_placing_data(self):
        astral_blur_pouet = PouetProduction.objects.create(
            name="Astral Blur", pouet_id=1, last_seen_at='2021-11-01 00:00:00'
        )
        compo_type, created = CompetitionType.objects.get_or_create(
            pouet_id=95, defaults={'name': 'pc demo'}
        )

        the_gathering = Party.objects.create(name="The Gathering", pouet_id=43)
        astral_blur_pouet.competition_placings.create(
            production = astral_blur_pouet,
            party = the_gathering,
            competition_type = compo_type,
            ranking = 3,
            year = 1997
        )
        self.assertEqual(astral_blur_pouet.competition_placings.count(), 1)
        self.assertEqual(
            astral_blur_pouet.competition_placings.first().ranking, 3
        )

        self.add_groups_response()

        ASTRAL_BLUR_BAD_PLACING = ASTRAL_BLUR.copy()
        BAD_PLACING = ASTRAL_BLUR['placings'][0].copy()
        BAD_PLACING['ranking'] = None
        ASTRAL_BLUR_BAD_PLACING['placings'] = [BAD_PLACING]
        self.add_prods_response(ASTRAL_BLUR_BAD_PLACING)

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet.refresh_from_db()
        self.assertEqual(astral_blur_pouet.competition_placings.count(), 1)
        self.assertIsNone(
            astral_blur_pouet.competition_placings.first().ranking
        )

    @responses.activate
    def test_keep_null_ranking_in_placing_data(self):
        astral_blur_pouet = PouetProduction.objects.create(
            name="Astral Blur", pouet_id=1, last_seen_at='2021-11-01 00:00:00'
        )
        compo_type, created = CompetitionType.objects.get_or_create(
            pouet_id=95, defaults={'name': 'pc demo'}
        )

        the_gathering = Party.objects.create(name="The Gathering", pouet_id=43)
        astral_blur_pouet.competition_placings.create(
            production = astral_blur_pouet,
            party = the_gathering,
            competition_type = compo_type,
            ranking = None,
            year = 1997
        )
        self.assertEqual(astral_blur_pouet.competition_placings.count(), 1)
        self.assertIsNone(
            astral_blur_pouet.competition_placings.first().ranking
        )

        self.add_groups_response()

        ASTRAL_BLUR_BAD_PLACING = ASTRAL_BLUR.copy()
        BAD_PLACING = ASTRAL_BLUR['placings'][0].copy()
        BAD_PLACING['ranking'] = None
        ASTRAL_BLUR_BAD_PLACING['placings'] = [BAD_PLACING]
        self.add_prods_response(ASTRAL_BLUR_BAD_PLACING)

        with captured_stdout():
            call_command('fetch_pouet_data')

        astral_blur_pouet.refresh_from_db()
        self.assertEqual(astral_blur_pouet.competition_placings.count(), 1)
        self.assertIsNone(
            astral_blur_pouet.competition_placings.first().ranking
        )
