from .base import *

DATABASES['default']['PORT'] = 4800
DATABASES['default']['USER'] = 'demozoo'
DATABASES['geonameslite']['PORT'] = 4800
DATABASES['geonameslite']['USER'] = 'demozoo'

DEBUG = False
EMAIL_HOST = 'localhost'

INSTALLED_APPS = list(INSTALLED_APPS) + ['django_gevent_deploy']

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'VHostCallingFormat'

GEVENT_ADDR_PORT = "localhost:4801"

BROKER_URL = 'redis://localhost:4803/0'

ALLOWED_HOSTS = ['localhost', 'dev.demozoo.org']

USE_PYGAME_IMAGE_CONVERSION = True

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

try:
	from .local import *
except ImportError:
	pass
