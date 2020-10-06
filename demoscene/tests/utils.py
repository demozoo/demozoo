from __future__ import absolute_import, unicode_literals

import os.path
import shutil

from django.conf import settings


TEST_MEDIA_DIR = os.path.join(os.path.join(settings.FILEROOT, 'test_media'))


class MediaTestMixin(object):
    def setUp(self):
        super(MediaTestMixin, self).setUp()
        shutil.rmtree(TEST_MEDIA_DIR, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(TEST_MEDIA_DIR, ignore_errors=True)
        super(MediaTestMixin, self).tearDown()
