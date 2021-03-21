from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Nick
from platforms.models import Platform
from productions.models import Production, ProductionType


class TestIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        tracked_music = ProductionType.objects.get(name='Tracked Music').id
        zx = Platform.objects.get(name='ZX Spectrum').id
        response = self.client.get('/music/?platform=%d&production_type=%d' % (zx, tracked_music))
        self.assertEqual(response.status_code, 200)


class TestShowMusic(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        cybrev.links.create(
            link_class='ModlandFile', parameter='/artists/gasman/cybernoids_revenge.vtx', is_download_link=True
        )
        response = self.client.get('/music/%d/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_get_with_artwork(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        cybrev.links.create(
            link_class='ModlandFile', parameter='/artists/gasman/cybernoids_revenge.vtx', is_download_link=True
        )
        cybrev.screenshots.create(
            original_url="http://example.com/orig.png",
            standard_url="http://example.com/standard.png",
            standard_width=400,
            standard_height=300,
        )

        response = self.client.get('/music/%d/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_non_music(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/music/%d/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)


class TestShowHistory(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/music/%d/history/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_non_music(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/music/%d/history/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/history/' % pondlife.id)


class TestCreateMusic(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/music/new/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/music/new/', {
            'title': 'Spacecake',
            'byline_search': 'Gasman',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'release_date': '6 feb 2010',
            'type': ProductionType.objects.get(name='Tracked Music').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/music/%d/' % Production.objects.get(title='Spacecake').id)
