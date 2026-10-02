from django.contrib.auth.models import User
from django.test import TestCase


class TestAPIKeysIndex(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_account_index(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/account/api_keys/")
        self.assertEqual(response.status_code, 200)
