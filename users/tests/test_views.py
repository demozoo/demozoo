from django.contrib.auth.models import User
from django.test import TestCase


class TestUsersIndex(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 200)

    def test_get_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/users/")
        self.assertRedirects(response, "/")


class TestShowUser(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        testuser = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.get("/users/%d/" % testuser.id)
        self.assertEqual(response.status_code, 200)


class TestRegistrationViews(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_reset_password(self):
        response = self.client.get("/account/forgotten_password/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset password - Demozoo")
