from django.contrib.auth.models import User
from django.test import TestCase


class TestLatestActivity(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/latest_activity/')
        self.assertEqual(response.status_code, 200)


class TestErrorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', email='testuser@example.com', password='12345')

    def test_unauthorised(self):
        response = self.client.get('/error/')
        self.assertRedirects(response, '/')

    def test_get(self):
        self.client.login(username='testuser', password='12345')
        with self.assertRaises(Exception):
            self.client.get('/error/')


class Test404Test(TestCase):
    def test_get(self):
        response = self.client.get('/404/')
        self.assertEqual(response.status_code, 200)


class TestRecentEdits(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/edits/')
        self.assertEqual(response.status_code, 200)
