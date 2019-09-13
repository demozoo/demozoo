from .base import *

DATABASES['default']['USER'] = 'demozoo'
DATABASES['default']['NAME'] = 'demozoo_staging'

DEBUG = False
EMAIL_HOST = 'localhost'

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'VHostCallingFormat'

BROKER_URL = 'redis://localhost:6379/1'

ALLOWED_HOSTS = ['localhost', 'staging.demozoo.org']

BASE_URL = 'https://staging.demozoo.org'

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
            'filename': '/home/demozoo/log/staging-app.log',
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
