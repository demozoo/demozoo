from django.test import TestCase


class TestLatestActivity(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/latest_activity/')
        self.assertEqual(response.status_code, 200)


class TestRecentEdits(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/edits/')
        self.assertEqual(response.status_code, 200)
