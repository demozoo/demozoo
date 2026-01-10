import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.html import escape

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
        # initially the "rating count" filter should be set to "0" (no ratings)
        self.assertContains(response, '<option value="0" selected>Not been rated yet</option>')

        # non-jurors cannot access the award page
        self.client.login(username="non_juror", password="12345")
        response = self.client.get("/awards/meteoriks-2020/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Welcome, jury member!")
        self.assertNotContains(response, "Production screening")
        self.assertContains(response, "Recommendations are closed right now.")

    def test_award_page_when_all_prods_screened_once(self):
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        self.meteoriks.screening_decisions.create(
            user=self.juror,
            production=prod,
            is_accepted=True,
        )
        self.client.login(username="juror", password="67890")
        response = self.client.get("/awards/meteoriks-2020/")
        # if all productions have been screened at least once, the "rating count"
        # filter should default to "N" (one Nay only)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<option value="N" selected>One Nay only</option>')

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
        cracktro = ProductionType.objects.get(name="Cracktro")

        self.client.login(username="juror", password="67890")

        url = f"/awards/meteoriks-2020/screening/?platforms={zx_spectrum.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

        response = self.client.get(f"/awards/meteoriks-2020/screening/?platforms={c64.id}", follow=True)
        self.assertRedirects(response, f"/awards/meteoriks-2020/?platforms={c64.id}")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        url = f"/awards/meteoriks-2020/screening/?production_types={demo.id}&production_types={cracktro.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{escape(url)}"')

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

    def test_filter_by_rating_count_one_nay_only(self):
        other_juror = User.objects.create_user(username="other_juror", password="54321")
        self.meteoriks.jurors.create(user=other_juror)
        other_other_juror = User.objects.create_user(username="other_other_juror", password="54321")
        self.meteoriks.jurors.create(user=other_other_juror)

        self.client.login(username="juror", password="67890")
        url = "/awards/meteoriks-2020/screening/?rating_count=N"

        # prods with no decisions should not show
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/?rating_count=N")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        # prods with one Nay only should show
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        decision = self.meteoriks.screening_decisions.create(
            user=other_juror,
            production=prod,
            is_accepted=False,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

        # prods with one Yay only should not show
        decision.is_accepted = True
        decision.save()
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/?rating_count=N")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        # prods with more than one decision should not show
        decision.is_accepted = False
        decision.save()
        self.meteoriks.screening_decisions.create(
            user=other_other_juror,
            production=prod,
            is_accepted=False,
        )
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/?rating_count=N")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

    def test_filter_by_rating_count_at_least_one_yay(self):
        other_juror = User.objects.create_user(username="other_juror", password="54321")
        self.meteoriks.jurors.create(user=other_juror)
        other_other_juror = User.objects.create_user(username="other_other_juror", password="54321")
        self.meteoriks.jurors.create(user=other_other_juror)

        self.client.login(username="juror", password="67890")
        url = "/awards/meteoriks-2020/screening/?rating_count=Y"

        # prods with no decisions should not show
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/awards/meteoriks-2020/?rating_count=Y")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")

        # prods with a Yay should show
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        self.meteoriks.screening_decisions.create(
            user=other_juror,
            production=prod,
            is_accepted=True,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

    def test_filter_by_platform_group(self):
        oldschool = self.meteoriks.series.platform_groups.get(name="Oldschool")
        newschool = self.meteoriks.series.platform_groups.get(name="Newschool")

        self.client.login(username="juror", password="67890")

        url = f"/awards/meteoriks-2020/screening/?platform_group={oldschool.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

        url = f"/awards/meteoriks-2020/screening/?platform_group={newschool.id}"
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, f"/awards/meteoriks-2020/?platform_group={newschool.id}")
        self.assertContains(response, "There are no productions that fit the chosen criteria.")
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        prod.platforms.clear()
        # the newschool group includes productions with no platform, so it should now show
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # form action url should preserve the filter
        self.assertContains(response, f'action="{url}"')

    def test_invalid_filter(self):
        self.client.login(username="juror", password="67890")

        url = "/awards/meteoriks-2020/screening/?platforms=AMIGAAAAA"
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

        url = f"/awards/meteoriks-2020/screening/?platforms={zx_spectrum.id}"
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
            f"/awards/meteoriks-2020/screening/?platforms={zx_spectrum.id}",
            {"production_id": production_id, "accept": "yes"},
            follow=True,
        )
        self.assertRedirects(response, f"/awards/meteoriks-2020/?platforms={zx_spectrum.id}")
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

    def test_screening_review_page(self):
        # non-jurors cannot access the screening page
        self.client.login(username="non_juror", password="12345")
        response = self.client.get("/awards/meteoriks-2020/screening/review/")
        self.assertEqual(response.status_code, 403)

        self.client.login(username="juror", password="67890")
        response = self.client.get("/awards/meteoriks-2020/screening/review/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your screened productions")

        # if no productions have been screened, it should show a message
        self.assertContains(response, "You have not screened any productions yet.")

        # screen a production and check the review page again
        production_id = Production.objects.get(title="The Brexecutable Music Compo Is Over").id
        self.meteoriks.screening_decisions.create(
            user=self.juror,
            production_id=production_id,
            is_accepted=True,
        )
        response = self.client.get("/awards/meteoriks-2020/screening/review/")
        self.assertContains(response, "The Brexecutable Music Compo Is Over")

        response = self.client.get("/awards/meteoriks-2020/screening/review/?decision=yay")
        self.assertContains(response, "The Brexecutable Music Compo Is Over")
        response = self.client.get("/awards/meteoriks-2020/screening/review/?decision=nay")
        self.assertNotContains(response, "The Brexecutable Music Compo Is Over")

    def test_screening_review_page_with_decision_change(self):
        production_id = Production.objects.get(title="The Brexecutable Music Compo Is Over").id
        decision = self.meteoriks.screening_decisions.create(
            user=self.juror,
            production_id=production_id,
            is_accepted=True,
        )

        url = f"/awards/meteoriks-2020/screening/review/{decision.id}/"
        # non-jurors cannot access the screening review change page
        self.client.login(username="non_juror", password="12345")
        response = self.client.post(url, {"decision": "nay"})
        self.assertEqual(response.status_code, 403)

        self.client.login(username="juror", password="67890")
        response = self.client.post(url, {"decision": "nay"})
        self.assertRedirects(response, "/awards/meteoriks-2020/screening/review/")
        decision.refresh_from_db()
        self.assertFalse(decision.is_accepted)

        response = self.client.post(f"{url}?page=2", {"decision": "skip"})
        self.assertRedirects(response, "/awards/meteoriks-2020/screening/review/?page=2")
        self.assertFalse(ScreeningDecision.objects.filter(id=decision.id).exists())

    def test_screening_production_page(self):
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        zx_spectrum = Platform.objects.get(name="ZX Spectrum")

        # jurors can access the screening page
        self.client.login(username="juror", password="67890")
        response = self.client.get(f"/awards/meteoriks-2020/screening/{prod.id}/?platforms={zx_spectrum.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Meteoriks 2020 - Screening")
        self.assertContains(response, "The Brexecutable Music Compo Is Over")
        # form action url should preserve the filter
        self.assertContains(response, f'action="/awards/meteoriks-2020/screening/?platforms={zx_spectrum.id}"')

        # cannot access the page if the production is not screenable
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get(f"/awards/meteoriks-2020/screening/{pondlife.id}/")
        self.assertEqual(response.status_code, 404)

        # non-jurors cannot access the screening page
        self.client.login(username="non_juror", password="12345")
        response = self.client.get(f"/awards/meteoriks-2020/screening/{prod.id}/")
        self.assertEqual(response.status_code, 403)

    def test_screening_comments(self):
        prod = Production.objects.get(title="The Brexecutable Music Compo Is Over")

        # non-jurors cannot comment
        self.client.login(username="non_juror", password="12345")
        response = self.client.post(
            f"/awards/meteoriks-2020/screening/{prod.id}/comment/",
            {"comment": "This is a test comment."},
        )
        self.assertEqual(response.status_code, 403)

        self.client.login(username="juror", password="67890")

        response = self.client.post(
            f"/awards/meteoriks-2020/screening/{prod.id}/comment/",
            {"comment": "This is a test comment."},
            follow=True,
        )
        self.assertRedirects(response, f"/awards/meteoriks-2020/screening/{prod.id}/")
        self.assertContains(response, "This is a test comment.")
        self.assertTrue(prod.screening_comments.filter(user=self.juror, comment="This is a test comment.").exists())

    def test_screening_report_page(self):
        # non-jurors cannot access the screening page
        self.client.login(username="non_juror", password="12345")
        response = self.client.get("/awards/meteoriks-2020/screening/report/")
        self.assertEqual(response.status_code, 403)

        self.client.login(username="juror", password="67890")
        response = self.client.get("/awards/meteoriks-2020/screening/report/")
        self.assertEqual(response.status_code, 200)
