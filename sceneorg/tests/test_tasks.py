import datetime
from unittest.mock import patch

from django.test import TestCase
from freezegun import freeze_time

from sceneorg.models import Directory, File
from sceneorg.tasks import fetch_new_sceneorg_files, scan_dir_listing


class TestTasks(TestCase):
    @freeze_time('2020-02-02')
    @patch('time.sleep')
    def test_fetch_new_sceneorg_files(self, sleep):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime.now())
        demos_dir = Directory.objects.create(path='/demos/', parent=root_dir, last_seen_at=datetime.datetime.now())
        File.objects.create(path='/demos/zz-t_01.diz', directory=demos_dir, last_seen_at=datetime.datetime(2019, 1, 1))
        fetch_new_sceneorg_files()
        self.assertTrue(
            File.objects.filter(path='/demos/zz-t_01.diz', last_seen_at__gt=datetime.datetime(2020, 1, 1)).exists()
        )
        self.assertTrue(
            File.objects.filter(path='/demos/artists/lazarus/lazarus-taxi-247-compo-version.diz').exists()
        )

    def test_nonsuccess_response(self):
        with self.assertLogs() as captured:
            fetch_new_sceneorg_files(days=999)
        self.assertIn("scene.org API request returned non-success!", captured.records[0].getMessage())

    @freeze_time('2020-02-02')
    @patch('sceneorg.tasks.parse_all_dirs')
    def test_scan_dir_listing(self, parse_all_dirs):
        root_dir = Directory.objects.create(path='/', last_seen_at=datetime.datetime(2020, 1, 1))
        Directory.objects.create(
            path='/demos/', parent=root_dir, last_seen_at=datetime.datetime(2020, 1, 1)
        )
        warez_dir = Directory.objects.create(
            path='/warez/', parent=root_dir, last_seen_at=datetime.datetime(2020, 1, 1)
        )
        Directory.objects.create(
            path='/warez/games/', parent=warez_dir, last_seen_at=datetime.datetime(2020, 1, 1)
        )
        File.objects.create(path='/uploading.txt', directory=root_dir, last_seen_at=datetime.datetime(2020, 1, 1))
        File.objects.create(
            path='/world-domination-plans.txt', directory=root_dir, last_seen_at=datetime.datetime(2020, 1, 1)
        )

        parse_all_dirs.return_value = [
            ('/', [
                ('demos', True, None),
                ('graphics', True, None),
                ('uploading.txt', False, '2129'),
            ]),
            ('/music/', [
                ('cocio.xm', False, '440607'),
            ]),
        ]
        scan_dir_listing()

        self.assertEqual(Directory.objects.get(path='/demos/').last_seen_at, datetime.datetime(2020, 2, 2))
        self.assertEqual(Directory.objects.get(path='/graphics/').last_seen_at, datetime.datetime(2020, 2, 2))
        self.assertEqual(File.objects.get(path='/music/cocio.xm').last_seen_at, datetime.datetime(2020, 2, 2))
        self.assertEqual(File.objects.get(path='/uploading.txt').last_seen_at, datetime.datetime(2020, 2, 2))
        self.assertTrue(Directory.objects.get(path='/warez/').is_deleted)
        self.assertTrue(Directory.objects.get(path='/warez/games/').is_deleted)
        self.assertTrue(File.objects.get(path='/world-domination-plans.txt').is_deleted)
