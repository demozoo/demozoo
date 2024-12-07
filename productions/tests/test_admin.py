from django.contrib.auth.models import User
from django.test import TestCase


class TestProductionAdmin(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")

    def test_get(self):
        response = self.client.get("/admin/productions/production/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Madrielle")
        self.assertContains(response, "Gasman / Raww Arse")
