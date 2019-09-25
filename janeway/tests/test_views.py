from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Releaser
from productions.models import Production, ProductionLink


class TestAuthorsIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')

    def test_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/janeway/authors/')
        self.assertEqual(response.status_code, 200)

    def test_get_full(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/janeway/authors/?full=1')
        self.assertEqual(response.status_code, 200)


class TestMatchAuthor(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')

    def test_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/janeway/authors/%d/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)


class TestProductionLink(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_post(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post('/janeway/production-link/', {
            'demozoo_id': self.pondlife.id,
            'janeway_id': 123,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ProductionLink.objects.filter(link_class='KestraBitworldRelease', parameter='123', production=self.pondlife).exists()
        )


class TestProductionUnlink(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        ProductionLink.objects.create(link_class='KestraBitworldRelease', parameter='123', production=self.pondlife)

    def test_post(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post('/janeway/production-unlink/', {
            'demozoo_id': self.pondlife.id,
            'janeway_id': 123,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            ProductionLink.objects.filter(link_class='KestraBitworldRelease', parameter='123', production=self.pondlife).exists()
        )
