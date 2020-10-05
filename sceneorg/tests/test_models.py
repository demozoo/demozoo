from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase

from sceneorg.models import Directory, File, FileTooBig


class TestModels(TestCase):
    def test_directory_str(self):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime(2020, 1, 1))
        self.assertEqual(str(root_dir), '/')

    def test_directory_newfiles(self):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime(2020, 1, 1))
        self.assertEqual(root_dir.new_files_url(42), 'https://www.scene.org/newfiles.php?dayint=42&dir=/')

    def test_file_str(self):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime(2020, 1, 1))
        uploading_txt = File.objects.create(path='/uploading.txt', directory=root_dir, last_seen_at=datetime.datetime(2020, 1, 1))
        self.assertEqual(str(uploading_txt), '/uploading.txt')

    def test_file_web_url(self):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime(2020, 1, 1))
        uploading_txt = File.objects.create(path='/uploading.txt', directory=root_dir, last_seen_at=datetime.datetime(2020, 1, 1))
        self.assertEqual(uploading_txt.web_url, 'https://files.scene.org/browse/uploading.txt')

    def test_fetch_oversized_file(self):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime(2020, 1, 1))
        bigfile_txt = File.objects.create(path='/bigfile.txt', directory=root_dir, last_seen_at=datetime.datetime(2020, 1, 1))
        with self.assertRaises(FileTooBig):
            data = bigfile_txt.fetched_data()
