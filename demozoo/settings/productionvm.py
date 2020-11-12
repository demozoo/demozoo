from __future__ import absolute_import, unicode_literals

from .base import *

DEBUG = False
EMAIL_HOST = 'localhost'

BROKER_URL = 'redis://localhost:6379/0'

ALLOWED_HOSTS = ['localhost', 'demozoo.org', 'www1.demozoo.org', 'zxdemo.org', 'www2.zxdemo.org']

# django-compressor offline compression
COMPRESS_OFFLINE = True
COMPRESS_OFFLINE_CONTEXT = {
    'base_template_with_ajax_option': 'base.html',
    'site_is_writeable': True,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(pathname)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/demozoo/log/app.log',
            'maxBytes': 10485760,
            'backupCount': 500,
            'formatter': 'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': [],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['default', 'mail_admins'],
            'level': 'DEBUG',
        }
    }
}

ZXDEMO_PLATFORM_IDS = [2]
