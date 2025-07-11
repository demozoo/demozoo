import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from awards.models import Event, ScreeningDecision
from platforms.models import Platform
from productions.models import Production, ProductionType


class TestScreening(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        self.non_juror = User.objects.create_user(username="non_juror", password="12345")
        self.juror = User.objects.create_user(username="juror", password="67890")
        self.meteoriks = Event.objects.get(slug="meteoriks-2020")
        self.meteoriks.recommendations_enabled = False
        self.meteoriks.save()
        self.meteoriks.jurors.create(user=self.juror)

    def test_menu_item(self):
        # menu item is not shown to non-jurors
        self.client.login(username="non_juror", password="12345")
        response = self.client.get("/")
        self.assertNotContains(response, "The Meteoriks 2020")

        # menu item is shown to jurors
        self.client.login(username="juror", password="67890")
        response = self.client.get("/")
        self.assertContains(response, "The Meteoriks 2020")

    def test_award_page(self):
        # jurors can access the award page
        self.client.login(username="juror", password="67890")
        response = self.client.get("/awards/meteoriks-2020/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome, jury member!")
        self.assertContains(response, "Production screening")

        # non-jurors cannot access the award page
        self.client.login(username="non_juror", password="12345")
        response = self.client.get("/awards/meteoriks-2020/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Welcome, jury member!")
        self.assertNotContains(response, "Production screening")
        self.assertContains(response, "Recommendations are closed right now.")

    def test_screening_page(self):
        # jurors can access the screening page
        self.client.login(username="juror", password="67890")
        response = self.client.get("/awards/meteoriks-2020/screening/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Meteoriks 2020 - Screening")

        # non-jurors cannot access the screening page
        self.client.login(username="non_juror", password="12345")
        response = self.client.get("/awards/meteoriks-2020/screening/")
        self.assertEqual(response.status_code, 403)

    def test_screening_page_without_screenable_productions(self):
        # if there are no screenable productions, the page should still load but show a message
        self.meteoriks.screenable_production_types.clear()
        self.meteoriks.save()

        self.client.login(username="juror", password="67890")
        response = self.client.get("/awards/meteoriks-2020/screening/", follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

    def test_screening_page_filtered(self):
        zx_spectrum = Platform.objects.get(name="ZX Spectrum")
        c64 = Platform.objects.get(name="Commodore 64")
        demo = ProductionType.objects.get(name="Demo")

        self.client.login(username="juror", password="67890")

        url = f"/awards/meteoriks-2020/screening/?platform={zx_spectrum.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

        response = self.client.get(f"/awards/meteoriks-2020/screening/?platform={c64.id}", follow=True)
        self.assertRedirects(response, f"/awards/meteoriks-2020/?platform={c64.id}")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        url = f"/awards/meteoriks-2020/screening/?production_type={demo.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{url}"')

        url = "/awards/meteoriks-2020/screening/?has_youtube=no"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{url}"')

        response = self.client.get("/awards/meteoriks-2020/screening/?has_youtube=yes", follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/?has_youtube=yes")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        prod.links.create(
            link_class="YoutubeVideo",
            parameter="DgNGVoQcN-Y",
            is_download_link=False,
        )
        url = "/awards/meteoriks-2020/screening/?has_youtube=yes"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{url}"')

    def test_filter_by_rating_count(self):
        other_juror = User.objects.create_user(username="other_juror", password="54321")
        self.meteoriks.jurors.create(user=other_juror)
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        self.meteoriks.screening_decisions.create(
            user=other_juror,
            production=prod,
            is_accepted=False,
        )
        self.client.login(username="juror", password="67890")

        url = "/awards/meteoriks-2020/screening/?rating_count=0"
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/?rating_count=0")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        url = "/awards/meteoriks-2020/screening/?rating_count=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

    def test_invalid_filter(self):
        self.client.login(username="juror", password="67890")

        url = "/awards/meteoriks-2020/screening/?platform=AMIGAAAAA"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should drop the invalid filter
        self.assertContains(response, 'action="/awards/meteoriks-2020/screening/"')

    def test_post_decision(self):
        zx_spectrum = Platform.objects.get(name="ZX Spectrum")
        self.client.login(username="juror", password="67890")

        # make sure we have one other eligible production to screen, so that we have
        # something to redirect to after the one we screen here
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.release_date_date = datetime.date(2019, 6, 1)
        pondlife.save()

        production_id = Production.objects.get(title="The Brexecutable Music Compo Is Over").id

        url = f"/awards/meteoriks-2020/screening/?platform={zx_spectrum.id}"
        response = self.client.post(
            url,
            {"production_id": production_id, "accept": "yes"},
            follow=True,
        )
        self.assertRedirects(response, url)
        self.assertTrue(
            ScreeningDecision.objects.filter(user=self.juror, production_id=production_id, is_accepted=True).exists()
        )
        self.assertContains(response, "Given a &#x27;Yay&#x27; to")

    def test_post_decision_on_last_prod(self):
        self.client.login(username="juror", password="67890")
        production_id = Production.objects.get(title="The Brexecutable Music Compo Is Over").id

        response = self.client.post(
            "/awards/meteoriks-2020/screening/",
            {"production_id": production_id, "accept": "yes"},
            follow=True,
        )
        self.assertRedirects(response, "/awards/meteoriks-2020/")
        self.assertTrue(
            ScreeningDecision.objects.filter(user=self.juror, production_id=production_id, is_accepted=True).exists()
        )
        self.assertContains(response, "Given a &#x27;Yay&#x27; to")
        self.assertContains(response, "You have screened all productions that fit the chosen criteria. Yay!")

    def test_post_decision_on_last_prod_filtered(self):
        self.client.login(username="juror", password="67890")
        production_id = Production.objects.get(title="The Brexecutable Music Compo Is Over").id
        zx_spectrum = Platform.objects.get(name="ZX Spectrum")

        response = self.client.post(
            f"/awards/meteoriks-2020/screening/?platform={zx_spectrum.id}",
            {"production_id": production_id, "accept": "yes"},
            follow=True,
        )
        self.assertRedirects(response, f"/awards/meteoriks-2020/?platform={zx_spectrum.id}")
        self.assertTrue(
            ScreeningDecision.objects.filter(user=self.juror, production_id=production_id, is_accepted=True).exists()
        )
        self.assertContains(response, "Given a &#x27;Yay&#x27; to")
        self.assertContains(response, "You have screened all productions that fit the chosen criteria. Yay!")

    def test_post_decision_on_ineligible_prod(self):
        self.client.login(username="juror", password="67890")
        production_id = Production.objects.get(title="Pondlife").id

        response = self.client.post(
            "/awards/meteoriks-2020/screening/",
            {"production_id": production_id, "accept": "yes"},
            follow=True,
        )
        self.assertRedirects(response, "/awards/meteoriks-2020/screening/")
        self.assertFalse(
            ScreeningDecision.objects.filter(user=self.juror, production_id=production_id, is_accepted=True).exists()
        )
        self.assertNotContains(response, "Given a &#x27;Yay&#x27; to")
