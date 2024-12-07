from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from common.utils.groklinks import Site, UrlPattern, grok_link_by_types
from demoscene.models import Releaser, ReleaserExternalLink
from parties.models import Party, PartyExternalLink
from productions.models import Production, ProductionLink


class TestSiteMatching(TestCase):
    def test_url_only(self):
        site = Site("Example", url="https://example.com/")
        self.assertTrue(site.matches_url(urlparse("http://example.com/foo")))
        self.assertTrue(site.matches_url(urlparse("https://www.example.com/foo")))
        self.assertFalse(site.matches_url(urlparse("ftp://example.com/foo")))
        self.assertFalse(site.matches_url(urlparse("http://www2.example.com/foo")))

    def test_ftp_only(self):
        site = Site("Example", url="ftp://example.com/")
        self.assertTrue(site.matches_url(urlparse("ftp://example.com/foo")))
        self.assertFalse(site.matches_url(urlparse("http://example.com/foo")))
        self.assertFalse(site.matches_url(urlparse("ftp://www.example.com/foo")))

    def test_url_and_schemes(self):
        site = Site("Example", url="https://www.example.com/", allowed_schemes=["https"])
        self.assertFalse(site.matches_url(urlparse("http://example.com/foo")))
        self.assertTrue(site.matches_url(urlparse("https://www.example.com/foo")))

    def test_url_and_hostnames(self):
        site = Site("Example", url="https://example.com/", allowed_hostnames=["example.com", "www2.example.com"])
        self.assertTrue(site.matches_url(urlparse("http://example.com/foo")))
        self.assertFalse(site.matches_url(urlparse("https://www.example.com/foo")))
        self.assertTrue(site.matches_url(urlparse("http://www2.example.com/foo")))

    def test_hostnames_and_schemes(self):
        site = Site(
            "Example", allowed_schemes=["https", "ftp"], allowed_hostnames=["www.example.com", "ftp.example.com"]
        )
        self.assertTrue(site.matches_url(urlparse("https://ftp.example.com/foo")))
        self.assertFalse(site.matches_url(urlparse("http://www.example.com/foo")))
        self.assertTrue(site.matches_url(urlparse("ftp://www.example.com/foo")))

    def test_cannot_have_path(self):
        with self.assertRaises(ImproperlyConfigured):
            Site("Example", url="https://www.example.com/woo")

        with self.assertRaises(ImproperlyConfigured):
            Site("Example", url="https://www.example.com/?woo=yay")

        with self.assertRaises(ImproperlyConfigured):
            Site("Example", url="https://www.example.com/#hoopla")


class TestLinkRecognition(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_sceneorg_folder(self):
        forever2e3 = Party.objects.get(name="Forever 2e3")
        link = PartyExternalLink(party=forever2e3)
        link.url = "ftp://ftp.scene.org/pub/parties/2000/forever00"
        self.assertEqual(link.link_class, "SceneOrgFolder")
        self.assertEqual(link.parameter, "/parties/2000/forever00/")
        self.assertEqual(str(link.link), "https://files.scene.org/browse/parties/2000/forever00/")

    def test_fujiology_folder(self):
        forever2e3 = Party.objects.get(name="Forever 2e3")
        link = PartyExternalLink(party=forever2e3)
        link.url = "ftp://fujiology.untergrund.net/users/ltk_tscc/fujiology/parties/2000/forever00"
        self.assertEqual(link.link_class, "FujiologyFolder")
        self.assertEqual(link.parameter, "/parties/2000/forever00/")

    def test_pouet_party_needs_query_params(self):
        forever2e3 = Party.objects.get(name="Forever 2e3")
        link = PartyExternalLink(party=forever2e3)
        link.url = "https://www.pouet.net/party.php?when=2000"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "https://www.pouet.net/party.php?when=2000")

    def test_pouet_group_id_must_be_numeric(self):
        gasman = Releaser.objects.get(name="Gasman")

        link = ReleaserExternalLink(releaser=gasman)
        link.url = "https://www.pouet.net/groups.php?which=123"
        self.assertEqual(link.link_class, "PouetGroup")
        self.assertEqual(link.parameter, 123)

        link = ReleaserExternalLink(releaser=gasman)
        link.url = "https://www.pouet.net/groups.php?which=amigaaaa"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "https://www.pouet.net/groups.php?which=amigaaaa")

    def test_artcity_artist(self):
        gasman = Releaser.objects.get(name="Gasman")

        link = ReleaserExternalLink(releaser=gasman)
        link.url = "http://artcity.bitfellas.org/index.php?a=artist&id=42"
        self.assertEqual(link.link_class, "ArtcityArtist")
        self.assertEqual(link.parameter, 42)

        # 'a' query param must be present
        link = ReleaserExternalLink(releaser=gasman)
        link.url = "http://artcity.bitfellas.org/index.php?x=artist&id=42"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "http://artcity.bitfellas.org/index.php?x=artist&id=42")

        # 'a' query param must be the expected value for the link type ('artist')
        link = ReleaserExternalLink(releaser=gasman)
        link.url = "http://artcity.bitfellas.org/index.php?a=artichoke&id=42"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "http://artcity.bitfellas.org/index.php?a=artichoke&id=42")

    def test_sceneorg_file(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=True)
        link.url = "https://www.scene.org/file_dl.php?url=ftp%3A//ftp.scene.org/pub/parties/2001/forever01/pondlife.zip"
        self.assertEqual(link.link_class, "SceneOrgFile")
        self.assertEqual(link.parameter, "/parties/2001/forever01/pondlife.zip")
        self.assertEqual(link.link.nl_url, "ftp://ftp.scene.org/pub/parties/2001/forever01/pondlife.zip")
        self.assertEqual(link.link.download_url, "ftp://ftp.scene.org/pub/parties/2001/forever01/pondlife.zip")
        self.assertEqual(link.link.nl_http_url, "http://archive.scene.org/pub/parties/2001/forever01/pondlife.zip")
        self.assertEqual(link.link.nl_https_url, "https://archive.scene.org/pub/parties/2001/forever01/pondlife.zip")

        link.url = "https://www.scene.org/file_dl.php?foo=http%3A//example.com/pondlife.zip"
        self.assertEqual(link.link_class, "BaseUrl")

        with self.assertRaises(TypeError):
            link.url = b"https://unicode.example.com/"

    def test_modland_file(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        link = ProductionLink(production=cybrev, is_download_link=True)
        link.url = "https://files.exotica.org.uk/modland/?file=artists/gasman/cybernoids_revenge.zip"
        self.assertEqual(link.link_class, "ModlandFile")
        self.assertEqual(link.parameter, "/artists/gasman/cybernoids_revenge.zip")

    def test_modarchive_other_params(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        link = ProductionLink(production=cybrev, is_download_link=True)
        link.url = "https://modarchive.org/index.php?request=view_by_moduleid&query=123"
        self.assertEqual(link.link_class, "ModarchiveModule")
        self.assertEqual(link.parameter, "123")
        link.url = "https://modarchive.org/index.php?request=view_by_instrument&query=keytar"
        self.assertEqual(link.link_class, "BaseUrl")
        link.url = "https://modarchive.org/index.php?request=view_by_moduleid&whichone=123"
        self.assertEqual(link.link_class, "BaseUrl")

    def test_youtube_video(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "https://www.youtube.com/watch?v=ldoVS0idTBw"
        self.assertEqual(link.link_class, "YoutubeVideo")
        self.assertEqual(link.parameter, "ldoVS0idTBw")
        self.assertEqual(str(link.link), "https://www.youtube.com/watch?v=ldoVS0idTBw")

        link.url = "https://www.youtube.com/watch?v=ldoVS0idTBw&t=250"
        self.assertEqual(link.link_class, "YoutubeVideo")
        self.assertEqual(link.parameter, "ldoVS0idTBw/250")
        self.assertEqual(str(link.link), "https://www.youtube.com/watch?v=ldoVS0idTBw&t=250")

        link.url = "https://www.youtu.be/ldoVS0idTBw"
        self.assertEqual(link.link_class, "YoutubeVideo")
        self.assertEqual(link.parameter, "ldoVS0idTBw")

        link.url = "https://www.youtu.be/ldoVS0idTBw?t=250"
        self.assertEqual(link.link_class, "YoutubeVideo")
        self.assertEqual(link.parameter, "ldoVS0idTBw/250")

        link.url = "https://www.youtube.com/embed/ldoVS0idTBw"
        self.assertEqual(link.link_class, "YoutubeVideo")
        self.assertEqual(link.parameter, "ldoVS0idTBw")

        link.url = "https://www.youtube.com/embed/ldoVS0idTBw?start=250"
        self.assertEqual(link.link_class, "YoutubeVideo")
        self.assertEqual(link.parameter, "ldoVS0idTBw/250")

        link.url = "https://www.youtube.com/watch?t=250"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "https://www.youtube.com/watch?t=250")

        link.url = "https://www.youtube.com/watch?v=r5sH2yZFY6whttp://csdb.dk/release/?id=51348"
        self.assertEqual(str(link.link), "https://www.youtube.com/watch?v=r5sH2yZFY6whttp://csdb.dk/release/?id=51348")
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "https://www.youtube.com/watch?v=r5sH2yZFY6whttp://csdb.dk/release/?id=51348")

    def test_discogs_release(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        link = ProductionLink(production=cybrev, is_download_link=True)
        link.url = "https://discogs.com/gasman/release/42"
        self.assertEqual(link.link_class, "DiscogsRelease")
        self.assertEqual(link.parameter, "42/gasman")
        self.assertEqual(str(link.link), "http://www.discogs.com/gasman/release/42")

    def test_github_directory(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "http://github.com/gasman/demos/tree/main/pondlife"
        self.assertEqual(link.link_class, "GithubDirectory")
        self.assertEqual(link.parameter, "gasman/demos/main/pondlife")
        self.assertEqual(str(link.link), "http://github.com/gasman/demos/tree/main/pondlife")

    def test_bandcamp_track(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        link = ProductionLink(production=cybrev, is_download_link=True)
        link.url = "https://gasman.bandcamp.com/track/cybernoids-revenge"
        self.assertEqual(link.link_class, "BandcampTrack")
        self.assertEqual(link.parameter, "gasman/cybernoids-revenge")
        self.assertEqual(str(link.link), "https://gasman.bandcamp.com/track/cybernoids-revenge")

    def test_speccypl_production(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "http://speccy.pl/archive/prod.php?id=14"
        self.assertEqual(link.link_class, "SpeccyPlProduction")
        self.assertEqual(link.parameter, 14)
        self.assertEqual(str(link.link), "http://speccy.pl/archive/prod.php?id=14")

    def test_speccypl_author(self):
        gasman = Releaser.objects.get(name="Gasman")

        link = ReleaserExternalLink(releaser=gasman)
        link.url = "http://speccy.pl/archive/author.php?id=24"
        self.assertEqual(link.link_class, "SpeccyPlAuthor")
        self.assertEqual(link.parameter, 24)

    def test_atariki_entry(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "http://atariki.krap.pl/index.php/Cool_Emotion"
        self.assertEqual(link.link_class, "AtarikiEntry")
        self.assertEqual(str(link.link), "http://atariki.krap.pl/index.php/Cool_Emotion")

        gasman = Releaser.objects.get(name="Gasman")
        link = ReleaserExternalLink(releaser=gasman)

        link.url = "http://atariki.krap.pl/index.php/Ars"
        self.assertEqual(link.link_class, "AtarikiEntry")

        forever2e3 = Party.objects.get(name="Forever 2e3")
        link = PartyExternalLink(party=forever2e3)
        link.url = "http://atariki.krap.pl/index.php/Lato_Ludzik%C3%B3w_1999"
        self.assertEqual(link.link_class, "AtarikiEntry")

    def test_dop_edition(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)
        link.url = "https://diskmag.conspiracy.hu/magazine/pain/#/edition=pain1207final"
        self.assertEqual(link.link_class, "DOPEdition")
        self.assertEqual(link.parameter, "pain/pain1207final")
        self.assertEqual(str(link.link), "https://diskmag.conspiracy.hu/magazine/pain/#/edition=pain1207final")

    def test_retroscene_events_release(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)
        link.url = "https://events.retroscene.org/zxgfx-03/main/2491"
        self.assertEqual(link.link_class, "EventsRetrosceneRelease")
        self.assertEqual(link.parameter, "zxgfx-03/main/2491")
        self.assertEqual(str(link.link), "https://events.retroscene.org/zxgfx-03/main/2491")

        # do not match paths under 'files'
        link = ProductionLink(production=pondlife, is_download_link=False)
        link.url = "https://events.retroscene.org/files/main/2491"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "https://events.retroscene.org/files/main/2491")
        self.assertEqual(str(link.link), "https://events.retroscene.org/files/main/2491")

        # do not match paths ending in a non-numeric component
        link.url = "https://events.retroscene.org/zxgfx-03/main/foo"
        self.assertEqual(link.link_class, "BaseUrl")
        self.assertEqual(link.parameter, "https://events.retroscene.org/zxgfx-03/main/foo")
        self.assertEqual(str(link.link), "https://events.retroscene.org/zxgfx-03/main/foo")

    def test_string_query_parameter(self):
        class ExampleLink(UrlPattern):
            site = Site("Example", url="https://example.com/")
            pattern = "/index.php?thing=<slug>"

        link = grok_link_by_types("https://example.com/index.php?thing=foo-bar", [ExampleLink])
        self.assertIsInstance(link, ExampleLink)
        self.assertEqual(link.param, "foo-bar")

    def test_bad_pattern(self):
        with self.assertRaises(ImproperlyConfigured):

            class ExampleLink1(UrlPattern):
                site = Site("Example", url="https://example.com/")
                pattern = "/index.php?first=<str>&second=<str>"

        with self.assertRaises(ImproperlyConfigured):

            class ExampleLink2(UrlPattern):
                site = Site("Example", url="https://example.com/")
                pattern = "/<int>/?id=<str>"


class TestEmbeds(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_base_url(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "http://example.com/gfsdfgsdf"
        self.assertEqual(link.link.get_embed_data(), None)

    def test_youtube(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "https://www.youtube.com/watch?v=ldoVS0idTBw"

        oembed_url = link.link.get_oembed_url(max_width=800, max_height=600)
        self.assertTrue(oembed_url.startswith("https://www.youtube.com/oembed"))
        self.assertIn("format=json", oembed_url)
        self.assertIn("maxwidth=800", oembed_url)
        self.assertIn("maxheight=600", oembed_url)

        embed_data = link.link.get_embed_data()
        self.assertEqual(embed_data["video_width"], 1280)
        self.assertEqual(embed_data["video_height"], 720)
        self.assertEqual(embed_data["thumbnail_width"], 480)
        self.assertEqual(embed_data["thumbnail_height"], 360)

        embed_html = link.link.get_embed_html(640, 480)
        self.assertEqual(
            embed_html,
            '<iframe width="640" height="480" src="https://www.youtube.com/embed/ldoVS0idTBw?autoplay=1" '
            'frameborder="0" allowfullscreen></iframe>',
        )

        link.url = "https://www.youtube.com/watch?v=ldoVS0idTBw&t=60"
        self.assertEqual(link.parameter, "ldoVS0idTBw/60")
        embed_html = link.link.get_embed_html(640, 480)
        self.assertEqual(
            embed_html,
            '<iframe width="640" height="480" src="https://www.youtube.com/embed/ldoVS0idTBw?start=60&amp;autoplay=1" '
            'frameborder="0" allowfullscreen></iframe>',
        )

        link.url = "https://www.youtube.com/watch?v=ldoVS0idTBw&t=1m30"
        self.assertEqual(link.parameter, "ldoVS0idTBw/1m30")
        embed_html = link.link.get_embed_html(640, 480)
        self.assertEqual(
            embed_html,
            '<iframe width="640" height="480" src="https://www.youtube.com/embed/ldoVS0idTBw?start=90&amp;autoplay=1" '
            'frameborder="0" allowfullscreen></iframe>',
        )

    def test_vimeo(self):
        pondlife = Production.objects.get(title="Pondlife")
        link = ProductionLink(production=pondlife, is_download_link=False)

        link.url = "https://vimeo.com/3156959"

        oembed_url = link.link.get_oembed_url(max_width=800, max_height=600)
        self.assertTrue(oembed_url.startswith("https://vimeo.com/api/oembed.json"))
        self.assertIn("maxwidth=800", oembed_url)
        self.assertIn("maxheight=600", oembed_url)

        embed_data = link.link.get_embed_data()
        self.assertEqual(embed_data["video_width"], 480)
        self.assertEqual(embed_data["video_height"], 270)
        self.assertEqual(embed_data["thumbnail_width"], 295)
        self.assertEqual(embed_data["thumbnail_height"], 166)

        embed_html = link.link.get_embed_html(640, 480)
        self.assertEqual(
            embed_html,
            '<iframe width="640" height="480" src="https://player.vimeo.com/video/3156959?autoplay=1" '
            'frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>',
        )
