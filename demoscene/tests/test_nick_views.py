from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from demoscene.models import Releaser


class TestMatchNick(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/nicks/match/?q=gas&autocomplete=true&sceners_only=true')
        self.assertEqual(response.status_code, 200)

        hprg = Releaser.objects.get(name='Hooy-Program')
        response = self.client.get(
            '/nicks/match/?q=gas&autocomplete=true&sceners_only=true&group_ids=%d' % hprg.id
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/nicks/match/?q=hooy&autocomplete=true&groups_only=true')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/nicks/match/?q=gasman&autocomplete=false&sceners_only=true')
        self.assertEqual(response.status_code, 200)


class TestMatchByline(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/nicks/byline_match/?q=gasman%2fhoo&autocomplete=true')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/nicks/byline_match/?q=gasman%2fhprg&autocomplete=false')
        self.assertEqual(response.status_code, 200)
