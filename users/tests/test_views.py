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
        response = self.client.get("/users/%d/" % testuser.id)
        self.assertEqual(response.status_code, 200)

    def test_track_ip(self):
        testuser = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

        # make a request with a forwarded IP address
        self.client.get(
            "/",
            headers={
                "x-forwarded-for": "8.8.8.8, 8.8.4.4",
            },
        )

        # ordinary user should not see the IP address
        response = self.client.get(
            "/users/%d/" % testuser.id,
            headers={
                "x-forwarded-for": "8.8.8.8, 8.8.4.4",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Last IP:")

        # staff user should see the IP address
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.get("/users/%d/" % testuser.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Last IP: 8.8.8.8")

    def test_get_as_staff_without_ip(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        testuser = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.get("/users/%d/" % testuser.id)
        self.assertEqual(response.status_code, 200)
        # user has no logged IP address, so staff user should not see the "Last IP" line
        self.assertNotContains(response, "Last IP:")


class TestRegistrationViews(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_reset_password(self):
        response = self.client.get("/account/forgotten_password/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset password - Demozoo")
