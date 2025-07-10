import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from awards.models import Event, ScreeningDecision
from productions.models import Production


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

    def test_post_decision(self):
        self.client.login(username="juror", password="67890")

        # make sure we have one other eligible production to screen, so that we have
        # something to redirect to after the one we screen here
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.release_date_date = datetime.date(2019, 6, 1)
        pondlife.save()

        production_id = Production.objects.get(title="The Brexecutable Music Compo Is Over").id

        response = self.client.post(
            "/awards/meteoriks-2020/screening/",
            {"production_id": production_id, "accept": "yes"},
            follow=True,
        )
        self.assertRedirects(response, "/awards/meteoriks-2020/screening/")
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
