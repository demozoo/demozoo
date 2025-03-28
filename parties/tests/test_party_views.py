from io import BytesIO

import PIL.Image
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from freezegun import freeze_time

from demoscene.models import Edit, Releaser
from demoscene.tests.utils import MediaTestMixin
from parties.models import (
    Competition,
    Organiser,
    Party,
    PartyExternalLink,
    PartySeries,
    PartySeriesExternalLink,
    ResultsFile,
)
from productions.models import Production


class TestShowIndex(TestCase):
    fixtures = ["tests/gasman.json"]

    @freeze_time("2000-05-05")
    def test_get_current_year_2000(self):
        response = self.client.get("/parties/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forever 2e3")

    def test_get_current_year(self):
        response = self.client.get("/parties/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Forever 2e3")

    def test_get_year(self):
        response = self.client.get("/parties/year/2000/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forever 2e3")


class TestShowPartiesByName(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        response = self.client.get("/parties/by_name/")
        self.assertEqual(response.status_code, 200)


class TestPartiesByDateRedirect(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        response = self.client.get("/parties/by_date/")
        self.assertRedirects(response, "/parties/")

        response = self.client.get("/parties/year/")
        self.assertRedirects(response, "/parties/")


class TestShowParty(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        party = Party.objects.get(name="Forever 2e3")
        response = self.client.get("/parties/%d/" % party.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman&#x27;s Shader Showdown Final entry on Shadertoy")

    def test_get_without_phase_name(self):
        party = Party.objects.get(name="Forever 2e3")
        phase = party.tournaments.first().phases.first()
        phase.name = ""
        phase.save()
        response = self.client.get("/parties/%d/" % party.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman&#x27;s Shader Showdown entry on Shadertoy")

    def test_organisers_panel(self):
        party = Party.objects.get(name="Revision 2011")
        response = self.client.get("/parties/%d/" % party.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")
        self.assertContains(response, "(Compo team)")


class TestShowPartyHistory(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        party = Party.objects.get(name="Forever 2e3")
        response = self.client.get("/parties/%d/history/" % party.id)
        self.assertEqual(response.status_code, 200)


class TestShowPartySeries(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        party_series = PartySeries.objects.get(name="Forever")

        madrielle = Production.objects.get(title="Madrielle")
        madrielle.screenshots.create(
            thumbnail_url="http://example.com/madrielle.thumb.png",
            thumbnail_width=130,
            thumbnail_height=100,
            standard_url="http://example.com/madrielle.standard.png",
            standard_width=320,
            standard_height=240,
        )

        response = self.client.get("/parties/series/%d/" % party_series.id)
        self.assertEqual(response.status_code, 200)


class TestShowPartySeriesHistory(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        party_series = PartySeries.objects.get(name="Forever")
        response = self.client.get("/parties/series/%d/history/" % party_series.id)
        self.assertEqual(response.status_code, 200)


class TestCreateParty(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_get(self):
        response = self.client.get("/parties/new/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/new/",
            {
                "name": "Evoke 2012",
                "start_date": "10 aug 2012",
                "end_date": "12 aug 2012",
                "party_series_name": "Evoke",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % Party.objects.get(name="Evoke 2012").id)

    def test_post_invalid(self):
        response = self.client.post(
            "/parties/new/",
            {
                "name": "",
                "start_date": "10 aug 2012",
                "end_date": "12 aug 2012",
                "party_series_name": "Evoke",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_inherit_party_series_data(self):
        ps = PartySeries.objects.get(name="Forever")
        ps.website = "http://forever8.net/"
        ps.external_links.create(link_class="TwitterAccount", parameter="forever8party")
        ps.external_links.create(link_class="PouetPartySeries", parameter="181")
        ps.save()

        response = self.client.post(
            "/parties/new/",
            {
                "name": "Forever 2005",
                "start_date": "18 mar 2005",
                "end_date": "20 mar 2005",
                "party_series_name": "Forever",
                "scene_org_folder": "/parties/2005/forever05/",
            },
        )
        party = Party.objects.get(name="Forever 2005")
        self.assertRedirects(response, "/parties/%d/" % party.id)
        self.assertEqual(party.website, "http://forever8.net/")
        self.assertEqual(party.external_links.get(link_class="TwitterAccount").parameter, "forever8party")
        self.assertEqual(party.external_links.get(link_class="PouetParty").parameter, "181/2005")
        self.assertEqual(party.external_links.get(link_class="SceneOrgFolder").parameter, "/parties/2005/forever05/")

    def test_party_series_inherits_website(self):
        ps = PartySeries.objects.get(name="Forever")
        ps.save()

        response = self.client.post(
            "/parties/new/",
            {
                "name": "Forever 2005",
                "start_date": "18 mar 2005",
                "end_date": "20 mar 2005",
                "party_series_name": "Forever",
                "website": "http://forever8.net/",
            },
        )
        party = Party.objects.get(name="Forever 2005")
        self.assertRedirects(response, "/parties/%d/" % party.id)
        self.assertEqual(PartySeries.objects.get(name="Forever").website, "http://forever8.net/")

    def test_post_ajax(self):
        response = self.client.post(
            "/parties/new/",
            {
                "name": "Revision 2012",
                "start_date": "6 april 2012",
                "end_date": "9 april 2012",
                "party_series_name": "Revision",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Party.objects.filter(name="Revision 2012").exists())


class TestEditParty(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get("/parties/%d/edit/" % self.party.id)
        self.assertRedirects(response, "/account/login/?next=/parties/%d/" % self.party.id)

    def test_get(self):
        response = self.client.get("/parties/%d/edit/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/%d/edit/" % self.party.id,
            {
                "name": "Forever 2000",
                "start_date": "17 march 2000",
                "end_date": "19 march 2000",
                "party_series_name": "Forever",
                "website": "http://forever.zeroteam.sk/",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(Party.objects.get(id=self.party.id).name, "Forever 2000")
        self.assertEqual(PartySeries.objects.get(name="Forever").website, "http://forever.zeroteam.sk/")

        edit = Edit.for_model(self.party, True).first()
        self.assertIn("Set name to 'Forever 2000'", edit.description)

        # no change => no edit log entry added
        edit_count = Edit.for_model(self.party, True).count()

        response = self.client.post(
            "/parties/%d/edit/" % self.party.id,
            {
                "name": "Forever 2000",
                "start_date": "17 march 2000",
                "end_date": "19 march 2000",
                "party_series_name": "Forever",
                "website": "http://forever.zeroteam.sk/",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(edit_count, Edit.for_model(self.party, True).count())

    def test_post_invalid(self):
        response = self.client.post(
            "/parties/%d/edit/" % self.party.id,
            {
                "name": "",
                "start_date": "17 march 2000",
                "end_date": "19 march 2000",
                "party_series_name": "Forever",
                "website": "http://forever.zeroteam.sk/",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_edit_all_fields(self):
        response = self.client.post(
            "/parties/%d/edit/" % self.party.id,
            {
                "name": "Forever 2000",
                "start_date": "18 march 2000",
                "end_date": "20 march 2000",
                "party_series_name": "Forever",
                "tagline": "doo doo doo do do doo",
                "location": "Oxford",
                "website": "http://forever8.net/",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(Party.objects.get(id=self.party.id).name, "Forever 2000")

        edit = Edit.for_model(self.party, True).first()
        self.assertIn("start date to 18 March 2000", edit.description)
        self.assertIn("end date to 20 March 2000", edit.description)
        self.assertIn("tagline to 'doo doo doo do do doo'", edit.description)
        self.assertIn("location to Oxford", edit.description)

    def test_edit_online_and_cancelled_flags(self):
        response = self.client.post(
            "/parties/%d/edit/" % self.party.id,
            {
                "name": "Forever 2000",
                "start_date": "17 march 2000",
                "end_date": "19 march 2000",
                "party_series_name": "Forever",
                "website": "http://forever.zeroteam.sk/",
                "is_online": "is_online",
                "is_cancelled": "is_cancelled",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(Party.objects.get(id=self.party.id).name, "Forever 2000")

        edit = Edit.for_model(self.party, True).first()
        self.assertIn("online to True", edit.description)
        self.assertIn("cancelled to True", edit.description)


class TestEditNotes(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")

    def test_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/parties/%d/edit_notes/" % self.party.id)
        self.assertRedirects(response, "/parties/%d/" % self.party.id)

    def test_get(self):
        response = self.client.get("/parties/%d/edit_notes/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/%d/edit_notes/" % self.party.id,
            {
                "notes": "doo doo doo do do doo",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(Party.objects.get(id=self.party.id).notes, "doo doo doo do do doo")


class TestEditExternalLinks(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")

    def test_get(self):
        response = self.client.get("/parties/%d/edit_external_links/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/%d/edit_external_links/" % self.party.id,
            {
                "external_links-TOTAL_FORMS": 1,
                "external_links-INITIAL_FORMS": 0,
                "external_links-MIN_NUM_FORMS": 0,
                "external_links-MAX_NUM_FORMS": 1000,
                "external_links-0-url": "https://twitter.com/forever8party",
                "external_links-0-party": self.party.id,
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(PartyExternalLink.objects.filter(party=self.party, link_class="TwitterAccount").count(), 1)
        self.assertEqual(
            PartySeries.objects.get(name="Forever").external_links.get(link_class="TwitterAccount").parameter,
            "forever8party",
        )

    def test_post_unicode(self):
        response = self.client.post(
            "/parties/%d/edit_external_links/" % self.party.id,
            {
                "external_links-TOTAL_FORMS": 1,
                "external_links-INITIAL_FORMS": 0,
                "external_links-MIN_NUM_FORMS": 0,
                "external_links-MAX_NUM_FORMS": 1000,
                "external_links-0-url": "https://twitter.com/förever8party",
                "external_links-0-party": self.party.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "URL must be pure ASCII - try copying it from your browser location bar")

    def test_post_with_pouet_link(self):
        response = self.client.post(
            "/parties/%d/edit_external_links/" % self.party.id,
            {
                "external_links-TOTAL_FORMS": 2,
                "external_links-INITIAL_FORMS": 0,
                "external_links-MIN_NUM_FORMS": 0,
                "external_links-MAX_NUM_FORMS": 1000,
                "external_links-0-url": "https://twitter.com/forever8party",
                "external_links-0-party": self.party.id,
                "external_links-1-url": "https://www.pouet.net/party.php?which=181&when=2000",
                "external_links-1-party": self.party.id,
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(PartyExternalLink.objects.filter(party=self.party, link_class="TwitterAccount").count(), 1)
        self.assertEqual(PartyExternalLink.objects.filter(party=self.party, link_class="PouetParty").count(), 1)
        self.assertEqual(
            PartySeries.objects.get(name="Forever").external_links.get(link_class="TwitterAccount").parameter,
            "forever8party",
        )
        self.assertEqual(
            PartySeries.objects.get(name="Forever").external_links.get(link_class="PouetPartySeries").parameter, "181"
        )


class TestEditSeriesExternalLinks(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party_series = PartySeries.objects.get(name="Forever")

    def test_get(self):
        response = self.client.get("/parties/series/%d/edit_external_links/" % self.party_series.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/series/%d/edit_external_links/" % self.party_series.id,
            {
                "external_links-TOTAL_FORMS": 1,
                "external_links-INITIAL_FORMS": 0,
                "external_links-MIN_NUM_FORMS": 0,
                "external_links-MAX_NUM_FORMS": 1000,
                "external_links-0-url": "https://twitter.com/forever8party",
                "external_links-0-party_series": self.party_series.id,
            },
        )
        self.assertRedirects(response, "/parties/series/%d/" % self.party_series.id)
        self.assertEqual(
            PartySeriesExternalLink.objects.filter(party_series=self.party_series, link_class="TwitterAccount").count(),
            1,
        )

    def test_post_unicode(self):
        response = self.client.post(
            "/parties/series/%d/edit_external_links/" % self.party_series.id,
            {
                "external_links-TOTAL_FORMS": 1,
                "external_links-INITIAL_FORMS": 0,
                "external_links-MIN_NUM_FORMS": 0,
                "external_links-MAX_NUM_FORMS": 1000,
                "external_links-0-url": "https://twitter.com/förever8party",
                "external_links-0-party_series": self.party_series.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "URL must be pure ASCII - try copying it from your browser location bar")


class TestEditSeriesNotes(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        self.party_series = PartySeries.objects.get(name="Forever")

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get("/parties/series/%d/edit_notes/" % self.party_series.id)
        self.assertRedirects(response, "/account/login/?next=/parties/series/%d/edit_notes/" % self.party_series.id)

    def test_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/parties/series/%d/edit_notes/" % self.party_series.id)
        self.assertRedirects(response, "/parties/series/%d/" % self.party_series.id)

    def test_get(self):
        response = self.client.get("/parties/series/%d/edit_notes/" % self.party_series.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/series/%d/edit_notes/" % self.party_series.id,
            {
                "notes": "doo doo doo do do doo",
            },
        )
        self.assertRedirects(response, "/parties/series/%d/" % self.party_series.id)
        self.assertEqual(PartySeries.objects.get(id=self.party_series.id).notes, "doo doo doo do do doo")


class TestEditSeries(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party_series = PartySeries.objects.get(name="Forever")

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get("/parties/series/%d/edit/" % self.party_series.id)
        self.assertRedirects(response, "/account/login/?next=/parties/series/%d/" % self.party_series.id)

    def test_get(self):
        response = self.client.get("/parties/series/%d/edit/" % self.party_series.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/series/%d/edit/" % self.party_series.id,
            {
                "name": "For8ver",
                "website": "http://forever.zeroteam.sk/",
            },
        )
        self.assertRedirects(response, "/parties/series/%d/" % self.party_series.id)
        ps = PartySeries.objects.get(id=self.party_series.id)
        self.assertEqual(ps.website, "http://forever.zeroteam.sk/")

    def test_post_invalid(self):
        response = self.client.post(
            "/parties/series/%d/edit/" % self.party_series.id,
            {
                "name": "",
                "website": "http://forever.zeroteam.sk/",
            },
        )
        self.assertEqual(response.status_code, 200)
        ps = PartySeries.objects.get(id=self.party_series.id)
        self.assertEqual(ps.name, "Forever")


class TestAddCompetition(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")

    def test_get(self):
        response = self.client.get("/parties/%d/add_competition/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/%d/add_competition/" % self.party.id,
            {
                "name": "ZX Graphics",
                "shown_date": "18 march 2000",
            },
        )
        self.assertRedirects(
            response,
            "/competitions/%d/edit/" % Competition.objects.get(party__name="Forever 2e3", name="ZX Graphics").id,
        )

    def test_post_invalid(self):
        response = self.client.post(
            "/parties/%d/add_competition/" % self.party.id,
            {
                "name": "",
                "shown_date": "18 march 2000",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")


class TestShowResultsFile(MediaTestMixin, TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        party = Party.objects.get(name="Forever 2e3")
        results_file = ResultsFile.objects.create(
            party=party,
            file=File(name="forever2e3.txt", file=BytesIO(b"You get a car! You get a car! Everybody gets a car!")),
            filename="forever2e3.txt",
            filesize=100,
            sha1="1234123412341234",
        )

        response = self.client.get("/parties/%d/results_file/%d/" % (party.id, results_file.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You get a car! You get a car! Everybody gets a car!")

    def test_get_with_unknown_encoding(self):
        party = Party.objects.get(name="Forever 2e3")
        results_file = ResultsFile.objects.create(
            party=party,
            file=File(
                name="forever2e3.txt", file=BytesIO(b"You get a car! \xb0 You get a car! \xb0 Everybody gets a car!")
            ),
            filename="forever2e3.txt",
            filesize=100,
            sha1="1234123412341234",
        )

        response = self.client.get("/parties/%d/results_file/%d/" % (party.id, results_file.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You get a car! ░ You get a car! ░ Everybody gets a car!")


class TestAutocomplete(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        response = self.client.get("/parties/autocomplete/?term=forev")
        self.assertEqual(response.status_code, 200)


class TestEditInvitations(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")

    def test_get(self):
        response = self.client.get("/parties/%d/edit_invitations/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.post(
            "/parties/%d/edit_invitations/" % self.party.id,
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": pondlife.id,
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(self.party.invitations.count(), 1)

        edit = Edit.for_model(self.party, True).first()
        self.assertEqual("Set invitations to Pondlife", edit.description)

        # no change => no edit log entry added
        edit_count = Edit.for_model(self.party, True).count()
        response = self.client.post(
            "/parties/%d/edit_invitations/" % self.party.id,
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 1,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": pondlife.id,
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(edit_count, Edit.for_model(self.party, True).count())

    def test_post_with_empty(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.post(
            "/parties/%d/edit_invitations/" % self.party.id,
            {
                "form-TOTAL_FORMS": 2,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": pondlife.id,
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "",
                "form-1-production_id": "",
                "form-1-production_title": "Froob",
                "form-1-production_byline_search": "froob",
            },
        )
        # form is re-shown
        self.assertEqual(response.status_code, 200)


class TestEditReleases(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")

    def test_get(self):
        response = self.client.get("/parties/%d/edit_releases/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.post(
            "/parties/%d/edit_releases/" % self.party.id,
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": pondlife.id,
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "",
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        self.assertEqual(self.party.releases.count(), 1)

    def test_post_with_empty(self):
        response = self.client.post(
            "/parties/%d/edit_releases/" % self.party.id,
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": "",
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "pondlife",
            },
        )
        # form is re-shown
        self.assertEqual(response.status_code, 200)


class TestEditCompetition(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_get(self):
        party = Party.objects.get(name="Forever 2e3")
        competition = Competition.objects.get(party=party, name="ZX 1K Intro")
        response = self.client.get("/parties/%d/edit_competition/%d/" % (party.id, competition.id))
        self.assertRedirects(response, "/competitions/%d/edit/" % competition.id)


class TestEditShareImage(MediaTestMixin, TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")
        madrielle = Production.objects.get(title="Madrielle")
        self.madrielle_screenshot = madrielle.screenshots.create(
            thumbnail_url="http://example.com/madrielle.thumb.png",
            thumbnail_width=130,
            thumbnail_height=100,
            standard_url="http://example.com/madrielle.standard.png",
            standard_width=320,
            standard_height=240,
        )

    def test_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/parties/%d/edit_share_image/" % self.party.id)
        self.assertRedirects(response, "/")

    def test_get(self):
        response = self.client.get("/parties/%d/edit_share_image/" % self.party.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            (
                '<input type="radio" name="share_screenshot" value="%d" id="id_share_screenshot_0">'
                % self.madrielle_screenshot.id
            ),
            html=True,
        )
        self.assertContains(response, "http://example.com/madrielle.thumb.png")

    def test_post_upload(self):
        f = BytesIO()
        image = PIL.Image.new("RGBA", (200, 200), "white")
        image.save(f, "PNG")
        image_file = ImageFile(f, name="test.png")

        response = self.client.post(
            "/parties/%d/edit_share_image/" % self.party.id,
            {"share_image_file": SimpleUploadedFile("test.png", image_file.file.getvalue())},
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        party = Party.objects.get(id=self.party.id)
        self.assertTrue(party.share_image_file.name)
        self.assertTrue(party.share_image_file_url)
        self.assertEqual(party.share_image_url, party.share_image_file_url)
        Party.objects.get(id=self.party.id).share_image_file.delete()

    def test_post_select_screenshot_invalid(self):
        response = self.client.post(
            "/parties/%d/edit_share_image/" % self.party.id,
            {
                "share_screenshot": self.madrielle_screenshot.id,
            },
        )
        self.assertRedirects(response, "/parties/%d/" % self.party.id)
        party = Party.objects.get(id=self.party.id)
        self.assertEqual(party.share_screenshot, self.madrielle_screenshot)
        self.assertEqual(party.share_image_url, "http://example.com/madrielle.standard.png")

    def test_post_select_screenshot(self):
        response = self.client.post(
            "/parties/%d/edit_share_image/" % self.party.id,
            {
                "share_screenshot": -1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not one of the available choices")


class TestAddOrganiser(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        self.testuser = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Forever 2e3")
        self.gasman = Releaser.objects.get(name="Gasman")
        self.yerzmyey = Releaser.objects.get(name="Yerzmyey")

    def test_get(self):
        response = self.client.get("/parties/%d/add_organiser/" % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/%d/add_organiser/" % self.party.id,
            {
                "releaser_nick_search": "gasman",
                "releaser_nick_match_id": self.gasman.primary_nick.id,
                "releaser_nick_match_name": "gasman",
                "role": "Beamteam",
            },
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.assertEqual(1, Organiser.objects.filter(releaser=self.gasman, party=self.party).count())

    def test_post_invalid(self):
        response = self.client.post(
            "/parties/%d/add_organiser/" % self.party.id,
            {
                "releaser_nick_search": "",
                "releaser_nick_match_id": "",
                "releaser_nick_match_name": "",
                "role": "Beamteam",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_post_locked(self):
        response = self.client.post(
            "/parties/%d/add_organiser/" % self.party.id,
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "Beamteam",
            },
            follow=True,
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.assertEqual(0, Organiser.objects.filter(releaser=self.yerzmyey, party=self.party).count())
        self.assertContains(response, "cannot be added as an organiser")

    def test_post_locked_as_staff(self):
        self.testuser.is_staff = True
        self.testuser.save()

        response = self.client.post(
            "/parties/%d/add_organiser/" % self.party.id,
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "Beamteam",
            },
            follow=True,
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.assertEqual(1, Organiser.objects.filter(releaser=self.yerzmyey, party=self.party).count())


class TestEditOrganiser(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        self.testuser = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Revision 2011")
        self.gasman = Releaser.objects.get(name="Gasman")
        self.laesq = Releaser.objects.get(name="LaesQ")
        self.orga = Organiser.objects.get(party=self.party, releaser=self.gasman)
        self.yerzmyey = Releaser.objects.get(name="Yerzmyey")
        self.yerz_orga = Organiser.objects.create(party=self.party, releaser=self.yerzmyey)

    def test_get(self):
        response = self.client.get("/parties/%d/edit_organiser/%d/" % (self.party.id, self.orga.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editing Gasman as organiser of Revision 2011")

    def test_get_locked(self):
        response = self.client.get("/parties/%d/edit_organiser/%d/" % (self.party.id, self.yerz_orga.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be edited")

    def test_get_locked_as_staff(self):
        self.testuser.is_staff = True
        self.testuser.save()

        response = self.client.get("/parties/%d/edit_organiser/%d/" % (self.party.id, self.yerz_orga.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editing Yerzmyey as organiser of Revision 2011")

    def test_post(self):
        response = self.client.post(
            "/parties/%d/edit_organiser/%d/" % (self.party.id, self.orga.id),
            {
                "releaser_nick_search": "laesq",
                "releaser_nick_match_id": self.laesq.primary_nick.id,
                "releaser_nick_match_name": "laesq",
                "role": "Beamteam",
            },
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.orga.refresh_from_db()
        self.assertEqual(self.orga.role, "Beamteam")
        self.assertEqual(self.orga.releaser, self.laesq)

    def test_post_invalid(self):
        response = self.client.post(
            "/parties/%d/edit_organiser/%d/" % (self.party.id, self.orga.id),
            {
                "releaser_nick_search": "",
                "releaser_nick_match_id": "",
                "releaser_nick_match_name": "",
                "role": "Beamteam",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_post_locked(self):
        response = self.client.post(
            "/parties/%d/edit_organiser/%d/" % (self.party.id, self.yerz_orga.id),
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "Infoteam",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.yerz_orga.refresh_from_db()
        self.assertEqual(self.yerz_orga.role, "")

    def test_post_locked_as_staff(self):
        self.testuser.is_staff = True
        self.testuser.save()

        response = self.client.post(
            "/parties/%d/edit_organiser/%d/" % (self.party.id, self.yerz_orga.id),
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "Infoteam",
            },
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.yerz_orga.refresh_from_db()
        self.assertEqual(self.yerz_orga.role, "Infoteam")

    def test_changed_to_locked_scener(self):
        response = self.client.post(
            "/parties/%d/edit_organiser/%d/" % (self.party.id, self.orga.id),
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "Beamteam",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be added as an organiser")
        self.orga.refresh_from_db()
        self.assertEqual(self.orga.role, "Compo team")
        self.assertEqual(self.orga.releaser, self.gasman)

    def test_changed_to_locked_scener_as_staff(self):
        self.testuser.is_staff = True
        self.testuser.save()

        response = self.client.post(
            "/parties/%d/edit_organiser/%d/" % (self.party.id, self.orga.id),
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "Beamteam",
            },
            follow=True,
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.orga.refresh_from_db()
        self.assertEqual(self.orga.role, "Beamteam")
        self.assertEqual(self.orga.releaser, self.yerzmyey)


class TestRemoveOrganiser(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        self.testuser = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.party = Party.objects.get(name="Revision 2011")
        self.gasman = Releaser.objects.get(name="Gasman")
        self.orga = Organiser.objects.get(party=self.party, releaser=self.gasman)
        self.yerzmyey = Releaser.objects.get(name="Yerzmyey")
        self.yerz_orga = Organiser.objects.create(party=self.party, releaser=self.yerzmyey)

    def test_get(self):
        response = self.client.get("/parties/%d/remove_organiser/%d/" % (self.party.id, self.orga.id))
        self.assertEqual(response.status_code, 200)

    def test_get_locked(self):
        response = self.client.get("/parties/%d/remove_organiser/%d/" % (self.party.id, self.yerz_orga.id))
        self.assertEqual(response.status_code, 403)

    def test_get_locked_as_staff(self):
        self.testuser.is_staff = True
        self.testuser.save()
        response = self.client.get("/parties/%d/remove_organiser/%d/" % (self.party.id, self.yerz_orga.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/parties/%d/remove_organiser/%d/" % (self.party.id, self.orga.id),
            {
                "yes": "yes",
            },
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.assertEqual(0, Organiser.objects.filter(releaser=self.gasman, party=self.party).count())

    def test_post_locked(self):
        response = self.client.post(
            "/parties/%d/remove_organiser/%d/" % (self.party.id, self.yerz_orga.id),
            {
                "yes": "yes",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(1, Organiser.objects.filter(releaser=self.yerzmyey, party=self.party).count())

    def test_post_locked_as_staff(self):
        self.testuser.is_staff = True
        self.testuser.save()
        response = self.client.post(
            "/parties/%d/remove_organiser/%d/" % (self.party.id, self.yerz_orga.id),
            {
                "yes": "yes",
            },
        )
        self.assertRedirects(response, "/parties/%d/?editing=organisers" % self.party.id)
        self.assertEqual(0, Organiser.objects.filter(releaser=self.yerzmyey, party=self.party).count())
