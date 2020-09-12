from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase
from mock import patch
from freezegun import freeze_time

from sceneorg.models import Directory, File
from sceneorg.tasks import fetch_new_sceneorg_files


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
        fetch_new_sceneorg_files(days=999)
