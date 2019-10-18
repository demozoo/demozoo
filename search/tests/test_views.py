from __future__ import absolute_import, unicode_literals

from django.test import TestCase


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
