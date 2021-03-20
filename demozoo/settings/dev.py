from __future__ import absolute_import, unicode_literals

import os

from .base import *  # noqa


DEBUG = True

BASE_URL = 'http://localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS = list(INSTALLED_APPS) + ['django_extensions']  # noqa

DEBUG_TOOLBAR_ENABLED = os.getenv('DEBUG_TOOLBAR_ENABLED', '1') != '0'

if DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa

ZXDEMO_PLATFORM_IDS = [2]
