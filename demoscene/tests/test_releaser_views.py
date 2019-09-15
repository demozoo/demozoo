from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Releaser
from productions.models import Credit, Production


class TestAddCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.laesq = Releaser.objects.get(name='LaesQ')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        response = self.client.get('/releasers/%d/add_credit/' % self.papaya_dezign.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/releasers/%d/add_credit/' % self.laesq.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/releasers/%d/add_credit/' % self.laesq.id, {
            'nick': self.laesq.primary_nick.id,
            'production_name': 'Pondlife',
            'production_id': self.pondlife.id,
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-category': 'Music',
            'credit-0-role': '',
        })
        self.assertRedirects(response, '/sceners/%d/' % self.laesq.id)
        self.assertEqual(Credit.objects.filter(production=self.pondlife, nick=self.laesq.primary_nick).count(), 1)


class TestEditCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        response = self.client.get(
            '/releasers/%d/edit_credit/%d/%d/' % (self.papaya_dezign.id, self.papaya_dezign.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            '/releasers/%d/edit_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        credit = Credit.objects.get(nick=self.gasman.primary_nick, production=self.pondlife)
        response = self.client.post(
            '/releasers/%d/edit_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id),
            {
                'nick': self.gasman.primary_nick.id,
                'production_name': 'Pondlife',
                'production_id': self.pondlife.id,
                'credit-TOTAL_FORMS': 1,
                'credit-INITIAL_FORMS': 1,
                'credit-MIN_NUM_FORMS': 0,
                'credit-MAX_NUM_FORMS': 1000,
                'credit-0-id': credit.id,
                'credit-0-category': 'Music',
                'credit-0-role': '',
            }
        )
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Credit.objects.get(production=self.pondlife, nick=self.gasman.primary_nick).category, 'Music')


class TestDeleteCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        response = self.client.get(
            '/releasers/%d/delete_credit/%d/%d/' % (self.papaya_dezign.id, self.papaya_dezign.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            '/releasers/%d/delete_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            '/releasers/%d/delete_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id),
            {'yes': 'yes'}
        )
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Credit.objects.filter(production=self.pondlife, nick=self.gasman.primary_nick).count(), 0)
