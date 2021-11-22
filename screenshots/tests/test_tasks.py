import os.path
import shutil

from django.conf import settings
from django.test import TestCase
from mock import patch
from PIL import Image

from mirror.actions import upload_dir
from mirror.models import ArchiveMember
from productions.models import Production, ProductionType, Screenshot
from screenshots.tasks import (
    create_screenshot_from_production_link, create_screenshot_versions_from_local_file, fetch_remote_screenshots,
    rebuild_screenshot
)


TEST_IMAGES_DIR = os.path.join(os.path.join(settings.FILEROOT, 'screenshots', 'tests', 'images'))


class TestCreateFromLocal(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('screenshots.processing.DefaultStorage')
    def test_run(self, DefaultStorage):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(production=skyrider)
        storage = DefaultStorage.return_value
        storage.url.return_value = 'http://example.com/screens/skyrider.png'

        dest_path = os.path.join(upload_dir, 'mr-scene.scr')
        shutil.copy(os.path.join(TEST_IMAGES_DIR, 'mr-scene.scr'), dest_path)

        create_screenshot_versions_from_local_file(
            screenshot.id, dest_path
        )
        screenshot.refresh_from_db()
        self.assertEqual(len(storage.save.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 256)
        self.assertFalse(os.path.isfile(dest_path))

    @patch('screenshots.processing.DefaultStorage')
    def test_extra_wide(self, DefaultStorage):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(production=skyrider)
        storage = DefaultStorage.return_value
        storage.url.return_value = 'http://example.com/screens/skyrider.png'

        dest_path = os.path.join(upload_dir, 'extrawide.png')
        Image.new('P', (1000, 30)).save(dest_path, 'png')

        create_screenshot_versions_from_local_file(
            screenshot.id, dest_path
        )
        screenshot.refresh_from_db()
        self.assertEqual(len(storage.save.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 1000)
        self.assertEqual(screenshot.standard_width, 400)
        self.assertEqual(screenshot.standard_height, 30)
        self.assertFalse(os.path.isfile(dest_path))

    @patch('screenshots.processing.DefaultStorage')
    def test_extra_wide_and_chonky(self, DefaultStorage):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(production=skyrider)
        storage = DefaultStorage.return_value
        storage.url.return_value = 'http://example.com/screens/skyrider.png'

        dest_path = os.path.join(upload_dir, 'extrawide.png')
        Image.new('P', (2000, 600)).save(dest_path, 'png')

        create_screenshot_versions_from_local_file(
            screenshot.id, dest_path
        )
        screenshot.refresh_from_db()
        self.assertEqual(len(storage.save.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 2000)
        self.assertEqual(screenshot.standard_width, 400)
        self.assertEqual(screenshot.standard_height, 150)
        self.assertFalse(os.path.isfile(dest_path))

    @patch('screenshots.processing.DefaultStorage')
    def test_extra_tall(self, DefaultStorage):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(production=skyrider)
        storage = DefaultStorage.return_value
        storage.url.return_value = 'http://example.com/screens/skyrider.png'

        dest_path = os.path.join(upload_dir, 'extrawide.png')
        Image.new('P', (30, 1000)).save(dest_path, 'png')

        create_screenshot_versions_from_local_file(
            screenshot.id, dest_path
        )
        screenshot.refresh_from_db()
        self.assertEqual(len(storage.save.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 30)
        self.assertEqual(screenshot.standard_width, 30)
        self.assertEqual(screenshot.standard_height, 300)
        self.assertFalse(os.path.isfile(dest_path))

    @patch('screenshots.processing.DefaultStorage')
    def test_extra_tall_and_chonky(self, DefaultStorage):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(production=skyrider)
        storage = DefaultStorage.return_value
        storage.url.return_value = 'http://example.com/screens/skyrider.png'

        dest_path = os.path.join(upload_dir, 'extrawide.png')
        Image.new('P', (800, 2000)).save(dest_path, 'png')

        create_screenshot_versions_from_local_file(
            screenshot.id, dest_path
        )
        screenshot.refresh_from_db()
        self.assertEqual(len(storage.save.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 800)
        self.assertEqual(screenshot.standard_width, 133)
        self.assertEqual(screenshot.standard_height, 300)
        self.assertFalse(os.path.isfile(dest_path))

    def test_missing_screenshot(self):
        dest_path = os.path.join(upload_dir, 'mr-scene.scr')
        shutil.copy(os.path.join(TEST_IMAGES_DIR, 'mr-scene.scr'), dest_path)

        create_screenshot_versions_from_local_file(
            9999, dest_path
        )
        self.assertFalse(os.path.isfile(dest_path))


class TestRebuildScreenshot(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('screenshots.tasks.upload_to_s3')
    def test_run(self, upload_to_s3):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(
            production=skyrider,
            original_url='http://kestra.exotica.org.uk/files/screenies/28000/154a.png',
            original_width=400, original_height=300
        )
        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        rebuild_screenshot(screenshot.id)
        screenshot.refresh_from_db()
        self.assertEqual(len(upload_to_s3.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 640)

    def test_missing_screenshot(self):
        rebuild_screenshot(9999)


class TestCreateFromProdLink(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('boto3.Session')
    @patch('screenshots.tasks.upload_to_s3')
    def test_run(self, upload_to_s3, Session):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://kestra.exotica.org.uk/files/screenies/28000/154a.png',
            is_download_link=True
        )

        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        create_screenshot_from_production_link(link.id)

        screenshot = skyrider.screenshots.first()
        self.assertEqual(len(upload_to_s3.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 640)

    def test_missing_link(self):
        create_screenshot_from_production_link(9999)

    def test_existing_screenshot(self):
        skyrider = Production.objects.get(title="Skyrider")
        screenshot = Screenshot.objects.create(
            production=skyrider,
            original_url='http://example.com/screens/skyrider.png',
            original_width=400, original_height=300
        )
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://kestra.exotica.org.uk/files/screenies/28000/154a.png',
            is_download_link=True,
            is_unresolved_for_screenshotting=True
        )

        create_screenshot_from_production_link(link.id)

        self.assertEqual(skyrider.screenshots.count(), 1)
        screenshot = skyrider.screenshots.first()
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        link.refresh_from_db()
        self.assertFalse(link.is_unresolved_for_screenshotting)

    def test_previous_bad_image(self):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://kestra.exotica.org.uk/files/screenies/28000/154a.png',
            is_download_link=True,
            has_bad_image=True
        )

        create_screenshot_from_production_link(link.id)
        self.assertEqual(skyrider.screenshots.count(), 0)

    @patch('boto3.Session')
    @patch('screenshots.tasks.upload_to_s3')
    def test_new_bad_image(self, upload_to_s3, Session):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/badimage.png',
            is_download_link=True
        )

        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        create_screenshot_from_production_link(link.id)

        link.refresh_from_db()
        self.assertTrue(link.has_bad_image)
        self.assertEqual(skyrider.screenshots.count(), 0)
        self.assertEqual(len(upload_to_s3.call_args_list), 0)

    @patch('boto3.Session')
    @patch('screenshots.tasks.upload_to_s3')
    def test_create_from_zipfile(self, upload_to_s3, Session):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/rubber.zip',
            is_download_link=True
        )

        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        create_screenshot_from_production_link(link.id)

        screenshot = skyrider.screenshots.first()
        self.assertEqual(len(upload_to_s3.call_args_list), 3)
        self.assertEqual(screenshot.original_url, 'http://example.com/screens/skyrider.png')
        self.assertEqual(screenshot.original_width, 320)

    @patch('boto3.Session')
    @patch('screenshots.tasks.upload_to_s3')
    def test_create_from_bad_zipfile(self, upload_to_s3, Session):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/badzipfile.zip',
            is_download_link=True
        )
        # create an archive listing so that fetch-from-mirror won't pre-empt the
        # BadZipFile error by trying to create one
        ArchiveMember.objects.create(
            archive_sha1='1714c638436d875760cba50fde5ad1382a042ef5',
            filename='bad-apple.png',
            file_size=42
        )

        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        create_screenshot_from_production_link(link.id)

        link.refresh_from_db()
        self.assertTrue(link.has_bad_image)
        self.assertEqual(skyrider.screenshots.count(), 0)
        self.assertEqual(len(upload_to_s3.call_args_list), 0)

    @patch('boto3.Session')
    @patch('screenshots.tasks.upload_to_s3')
    def test_create_from_zipfile_with_bad_image(self, upload_to_s3, Session):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/rubberbadimage.zip',
            is_download_link=True
        )

        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        create_screenshot_from_production_link(link.id)

        link.refresh_from_db()
        self.assertTrue(link.has_bad_image)
        self.assertEqual(skyrider.screenshots.count(), 0)
        self.assertEqual(len(upload_to_s3.call_args_list), 0)

    @patch('boto3.Session')
    @patch('screenshots.tasks.upload_to_s3')
    def test_create_from_zipfile_with_multiple_images(self, upload_to_s3, Session):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/badzipfile.zip',
            is_download_link=True
        )
        ArchiveMember.objects.create(
            archive_sha1='1714c638436d875760cba50fde5ad1382a042ef5',
            filename='bad-apple.png',
            file_size=42
        )
        ArchiveMember.objects.create(
            archive_sha1='1714c638436d875760cba50fde5ad1382a042ef5',
            filename='bad-apple-2.png',
            file_size=42
        )

        upload_to_s3.return_value = 'http://example.com/screens/skyrider.png'
        create_screenshot_from_production_link(link.id)

        link.refresh_from_db()
        self.assertTrue(link.is_unresolved_for_screenshotting)
        self.assertEqual(skyrider.screenshots.count(), 0)
        self.assertEqual(len(upload_to_s3.call_args_list), 0)


class TestFetchRemoteScreenshots(TestCase):
    fixtures = ['tests/gasman.json']

    @patch('screenshots.tasks.create_screenshot_from_production_link')
    def test_fetch_from_image(self, create_screenshot_from_production_link):
        skyrider = Production.objects.get(title="Skyrider")
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/skyrider.png',
            is_download_link=True
        )
        fetch_remote_screenshots()
        create_screenshot_from_production_link.delay.assert_called_once_with(link.id)

    @patch('screenshots.tasks.create_screenshot_from_production_link')
    def test_fetch_from_zip(self, create_screenshot_from_production_link):
        skyrider = Production.objects.get(title="Skyrider")
        skyrider.types.set([ProductionType.objects.get(name='Graphics')])
        link = skyrider.links.create(
            link_class='BaseUrl',
            parameter='http://example.com/skyrider.zip',
            is_download_link=True,
            file_for_screenshot='skyrider.png'
        )
        fetch_remote_screenshots()
        create_screenshot_from_production_link.delay.assert_called_once_with(link.id)
