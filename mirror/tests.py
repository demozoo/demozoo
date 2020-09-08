from __future__ import unicode_literals

from django.test import TestCase

from mirror.actions import FileTooBig, fetch_link
from mirror.models import Download
from productions.models import Production

class TestActions(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_fetch_content_length_too_big(self):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pretend-big-file.txt',
            is_download_link=True
        )
        with self.assertRaises(FileTooBig):
            fetch_link(link)

        self.assertTrue(
            Download.objects.filter(
                parameter='http://example.com/pretend-big-file.txt', error_type='FileTooBig'
            ).exists()
        )

    def test_fetch_actual_length_too_big(self):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/real-big-file.txt',
            is_download_link=True
        )
        with self.assertRaises(FileTooBig):
            fetch_link(link)

        self.assertTrue(
            Download.objects.filter(
                parameter='http://example.com/real-big-file.txt', error_type='FileTooBig'
            ).exists()
        )
