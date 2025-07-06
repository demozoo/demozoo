from django.contrib.auth.models import User
from django.test import TestCase

from awards.models import Event


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
