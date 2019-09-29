from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Nick
from platforms.models import Platform
from productions.models import Production, ProductionType


class TestIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        gfx = ProductionType.objects.get(name='Graphics').id
        zx = Platform.objects.get(name='ZX Spectrum').id
        response = self.client.get('/graphics/?platform=%d&production_type=%d' % (zx, gfx))
        self.assertEqual(response.status_code, 200)


class TestShowGraphics(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        skyrider = Production.objects.get(title="Skyrider")
        response = self.client.get('/graphics/%d/' % skyrider.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_non_graphics(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/graphics/%d/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)


class TestShowHistory(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        skyrider = Production.objects.get(title="Skyrider")
        response = self.client.get('/graphics/%d/history/' % skyrider.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_non_graphics(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/graphics/%d/history/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/history/' % pondlife.id)


class TestCreateGraphics(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/graphics/new/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/graphics/new/', {
            'title': 'Blue Only Mode',
            'byline_search': 'Gasman',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'release_date': '6 feb 2010',
            'type': ProductionType.objects.get(name='Graphics').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/graphics/%d/' % Production.objects.get(title='Blue Only Mode').id)
