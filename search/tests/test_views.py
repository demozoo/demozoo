from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from demoscene.models import Nick
from productions.models import Production


class TestSearch(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/search/?q=pondlife')
        self.assertEqual(response.status_code, 200)

    def test_bad_page_number(self):
        response = self.client.get('/search/?q=pondlife&page=amigaaaa')
        self.assertEqual(response.status_code, 200)

    def test_invalid_search(self):
        response = self.client.get('/search/?q=')
        self.assertEqual(response.status_code, 200)


class TestLiveSearch(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.screenshots.create(thumbnail_url='http://example.com/pondlife.thumb.png')

        response = self.client.get('/search/live/?q=pondli')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")

    def test_get_music(self):
        response = self.client.get('/search/live/?q=cybern&category=music')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cybernoid's Revenge")

    def test_get_scener(self):
        response = self.client.get('/search/live/?q=gasm&category=scener')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")

    def test_get_group(self):
        hprg = Nick.objects.get(name='Hooy-Program')
        hprg.differentiator = 'ZX'
        hprg.save()
        response = self.client.get('/search/live/?q=hooy&category=group')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hooy-Program")

    def test_get_party(self):
        response = self.client.get('/search/live/?q=forev&category=party')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forever 2e3")

    def test_no_query(self):
        response = self.client.get('/search/live/')
        self.assertEqual(response.status_code, 200)
