from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from pages.models import Page


class TestPageModel(TestCase):
    def test_get(self):
        page = Page(
            title="how to get 10 pikachu onto a train",
            slug="pikachu",
            body="poke 'em on"
        )

        self.assertEqual(str(page), "how to get 10 pikachu onto a train")


class TestPageView(TestCase):
    def test_get(self):
        Page.objects.create(
            title="how to get 10 pikachu onto a train",
            slug="pikachu",
            body="poke 'em on"
        )

        response = self.client.get('/pages/pikachu/')
        self.assertEqual(response.status_code, 200)
