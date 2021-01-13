from django.contrib.auth.models import User
from django.test import TestCase

from bbs.models import BBS


class TestIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/bbs/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StarPort")


class TestShow(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        bbs = BBS.objects.get(name='StarPort')
        response = self.client.get('/bbs/%d/' % bbs.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StarPort")


class TestCreate(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/bbs/new/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/bbs/new/', {
            'name': 'Eclipse',
            'location': '',
        })
        self.assertRedirects(response, '/bbs/%d/' % BBS.objects.get(name='Eclipse').id)
