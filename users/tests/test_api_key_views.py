from django.contrib.auth.models import User
from django.test import TestCase

from users.models import APIKey


class TestAPIKeysIndex(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_account_index(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/account/api_keys/")
        self.assertEqual(response.status_code, 200)


class TestAPIKeysCreate(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_get(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/account/api_keys/create/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post("/account/api_keys/create/", {"name": "Test API Key"}, follow=True)
        self.assertRedirects(response, "/account/api_keys/")
        self.assertTrue(self.user.api_keys.filter(name="Test API Key").exists())
        self.assertContains(response, "API key created successfully")


class TestAPIKeysRevoke(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.api_key, _ = APIKey.objects.create_key(name="Test API Key", user=self.user)

    def test_get(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(f"/account/api_keys/revoke/{self.api_key.id}/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(f"/account/api_keys/revoke/{self.api_key.id}/", {"yes": "yes"}, follow=True)
        self.assertRedirects(response, "/account/api_keys/")
        self.api_key.refresh_from_db()
        self.assertTrue(self.api_key.revoked)
        self.assertContains(response, "API key &#x27;Test API Key&#x27; revoked")

    def test_post_cancel(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(f"/account/api_keys/revoke/{self.api_key.id}/", {"no": "no"}, follow=True)
        self.assertRedirects(response, "/account/api_keys/")
        self.api_key.refresh_from_db()
        self.assertFalse(self.api_key.revoked)
