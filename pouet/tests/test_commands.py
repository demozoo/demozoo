import gzip
import json

import responses
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from freezegun import freeze_time

from demoscene.models import Releaser
from pouet.models import Group, GroupMatchInfo
from pouet.models import Production as PouetProduction
from productions.models import Production, ProductionType


@freeze_time('2021-11-01')
class TestFetchPouetData(TestCase):
    @responses.activate
    def test_run(self):
        group_json = json.dumps({
            "dump_date": "2021-10-27 04:30:01",
            "groups": [
                {
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
            ]
        })
        group_gzdata = gzip.compress(group_json.encode('utf-8'))
        responses.add(
            responses.GET, 'https://data.pouet.net/dumps/202110/pouetdatadump-groups-20211027.json.gz',
            body=group_gzdata, stream=True
        )

        prod_json = json.dumps({
            "dump_date": "2021-10-27 04:30:01",
            "prods": [
                {
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
                },
            ]
        })
        prod_gzdata = gzip.compress(prod_json.encode('utf-8'))
        responses.add(
            responses.GET, 'https://data.pouet.net/dumps/202110/pouetdatadump-prods-20211027.json.gz',
            body=prod_gzdata, stream=True
        )

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
