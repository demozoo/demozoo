from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from janeway.models import Author


class TestAuthorModel(TestCase):
    fixtures = ['tests/janeway.json']

    def test_str(self):
        spb = Author.objects.get(name="Spaceballs")
        self.assertEqual(str(spb), "Spaceballs")
