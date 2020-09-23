from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.test.utils import captured_stdout
from mock import patch

from productions.models import Production, ProductionLink


class TestFetchEmbedData(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('productions.tasks.fetch_production_link_embed_data')
    def test_run(self, fetch_production_link_embed_data):
        pondlife = Production.objects.get(title='Pondlife')
        # create with a bogus link_class to prevent fetch_production_link_embed_data
        # from being called on save()
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='1lFBXWxSrKE',
            is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(link_class='YoutubeVideo')

        with captured_stdout():
            call_command('fetch_embed_data')

        fetch_production_link_embed_data.delay.assert_called_once_with(link.id)


class TestMirrorMusicFiles(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('productions.management.commands.mirror_music_files.upload_to_s3')
    @patch('time.sleep')
    def test_run(self, sleep, upload_to_s3):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        link = cybrev.links.create(
            link_class='BaseUrl', parameter='http://example.com/cybrev.mod',
            is_download_link=True
        )
        upload_to_s3.return_value = 'https://media.demozoo.org/music/cybrev.mod'

        with captured_stdout():
            call_command('mirror_music_files')

        upload_to_s3.assert_called_once()
        self.assertTrue(
            cybrev.links.filter(
                link_class='BaseUrl',
                parameter='https://media.demozoo.org/music/cybrev.mod',
                is_download_link=True
            ).exists()
        )

    @patch('productions.management.commands.mirror_music_files.upload_to_s3')
    @patch('time.sleep')
    def test_already_playable(self, sleep, upload_to_s3):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        cybrev.links.create(
            link_class='BaseUrl', parameter='https://files.zxdemo.org/cybrev.stc',
            is_download_link=True
        )
        link = cybrev.links.create(
            link_class='BaseUrl', parameter='http://example.com/cybrev.mod',
            is_download_link=True
        )
        upload_to_s3.return_value = 'https://media.demozoo.org/music/cybrev.mod'

        with captured_stdout():
            call_command('mirror_music_files')

        upload_to_s3.assert_not_called()
        self.assertFalse(
            cybrev.links.filter(
                link_class='BaseUrl',
                parameter='https://media.demozoo.org/music/cybrev.mod',
                is_download_link=True
            ).exists()
        )

    @patch('productions.management.commands.mirror_music_files.upload_to_s3')
    @patch('time.sleep')
    def test_oversized(self, sleep, upload_to_s3):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        link = cybrev.links.create(
            link_class='BaseUrl', parameter='http://example.com/pretend-big-file.mod',
            is_download_link=True
        )
        upload_to_s3.return_value = 'https://media.demozoo.org/music/cybrev.mod'

        with captured_stdout():
            call_command('mirror_music_files')

        upload_to_s3.assert_not_called()
        self.assertFalse(
            cybrev.links.filter(
                link_class='BaseUrl',
                parameter='https://media.demozoo.org/music/cybrev.mod',
                is_download_link=True
            ).exists()
        )
