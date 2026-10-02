from django.contrib.auth.models import User
from django.test import TestCase


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
