from __future__ import absolute_import, unicode_literals

import os.path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from mock import patch
import responses

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


class TestRefetchEmbedData(TestCase):
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
            call_command('refetch_embed_data')

        fetch_production_link_embed_data.delay.assert_called_once_with(link.id)


class TestMirrorMusicFiles(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('productions.management.commands.mirror_music_files.upload_to_s3')
    @patch('time.sleep')
    def test_run(self, sleep, upload_to_s3):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        cybrev.links.create(
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
        cybrev.links.create(
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
        cybrev.links.create(
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


class TestPurgeDeadYoutubeLinks(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('productions.tasks.clean_dead_youtube_link')
    def test_run(self, clean_dead_youtube_link):
        pondlife = Production.objects.get(title='Pondlife')
        # create with a bogus link_class to prevent fetch_production_link_embed_data
        # from being called on save()
        link = pondlife.links.create(
            link_class='SpeccyWikiPage', parameter='1lFBXWxSrKE',
            is_download_link=False
        )
        ProductionLink.objects.filter(id=link.id).update(link_class='YoutubeVideo')

        with captured_stdout():
            call_command('purge_dead_youtube_links')

        clean_dead_youtube_link.delay.assert_called_once_with(link.id)


class TestFindEmulatableZxdemoProds(TestCase):
    fixtures = ['tests/gasman.json']

    @responses.activate
    def test_run(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.links.create(
            link_class='BaseUrl', parameter='https://files.zxdemo.org/pondlife2.txt',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='https://files.zxdemo.org/zxwister.zip',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='https://files.zxdemo.org/badzipfile.zip',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='https://files.zxdemo.org/brokenlink.zip',
            is_download_link=True
        )

        responses.add(
            responses.GET, 'https://files.zxdemo.org/pondlife2.txt',
            body="just a text file"
        )
        responses.add(
            responses.GET, 'https://files.zxdemo.org/badzipfile.zip',
            body="she wishes that she'd gone to the party on the sun"
        )
        path = os.path.join(settings.FILEROOT, 'mirror', 'test_media', 'zxwister.zip')  # noqa
        zxwister = open(path, 'rb')
        responses.add(
            responses.GET, 'https://files.zxdemo.org/zxwister.zip',
            body=zxwister
        )

        self.assertEqual(pondlife.emulator_configs.count(), 0)
        with captured_stdout():
            call_command('find_emulatable_zxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 1)
        with captured_stdout():
            call_command('find_emulatable_zxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 1)
        zxwister.close()


class TestFindEmulatableNonZxdemoProds(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.sleep')
    @patch('boto3.Session')
    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.upload_to_s3')
    def test_run_link_without_emulatable_file(self, upload_to_s3, Session, sleep):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.links.create(
            link_class='PouetProduction', parameter='1234',
            is_download_link=False
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife2.txt',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/real-big-file.txt',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/rubber.zip',
            is_download_link=True
        )
        upload_to_s3.return_value = 'http://s3.example.com/rubber.zip'
        self.assertEqual(pondlife.emulator_configs.count(), 0)
        with captured_stdout():
            call_command('find_emulatable_nonzxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 0)

    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.sleep')
    @patch('boto3.Session')
    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.upload_to_s3')
    def test_run_link_with_bad_zipfile(self, upload_to_s3, Session, sleep):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/badzipfile.zip',
            is_download_link=True
        )
        upload_to_s3.return_value = 'http://s3.example.com/badzipfile.zip'
        self.assertEqual(pondlife.emulator_configs.count(), 0)
        with captured_stdout():
            call_command('find_emulatable_nonzxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 0)

    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.sleep')
    @patch('boto3.Session')
    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.upload_to_s3')
    def test_run_link_with_emulatable_file_in_zip(self, upload_to_s3, Session, sleep):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.links.create(
            link_class='PouetProduction', parameter='1234',
            is_download_link=False
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife2.txt',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/badtapfile.tap',
            is_download_link=True
        )
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/zxwister.zip',
            is_download_link=True
        )
        upload_to_s3.return_value = 'http://s3.example.com/zxwister.zip'
        self.assertEqual(pondlife.emulator_configs.count(), 0)
        with captured_stdout():
            call_command('find_emulatable_nonzxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 1)


    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.sleep')
    @patch('boto3.Session')
    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.upload_to_s3')
    def test_run_link_with_multiple_emulatable_files_in_zip(self, upload_to_s3, Session, sleep):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/zxwister2.zip',
            is_download_link=True
        )
        upload_to_s3.return_value = 'http://s3.example.com/zxwister2.zip'
        self.assertEqual(pondlife.emulator_configs.count(), 0)
        with captured_stdout():
            call_command('find_emulatable_nonzxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 0)

    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.sleep')
    @patch('boto3.Session')
    @patch('productions.management.commands.find_emulatable_nonzxdemo_prods.upload_to_s3')
    def test_run_link_with_emulatable_file_not_in_zip(self, upload_to_s3, Session, sleep):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife.tap',
            is_download_link=True
        )
        upload_to_s3.return_value = 'http://s3.example.com/pondlife.tap'
        self.assertEqual(pondlife.emulator_configs.count(), 0)
        with captured_stdout():
            call_command('find_emulatable_nonzxdemo_prods')
        self.assertEqual(pondlife.emulator_configs.count(), 1)
