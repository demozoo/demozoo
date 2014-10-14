from .base import *

DATABASES['default']['USER'] = 'demozoo'
DATABASES['geonameslite']['USER'] = 'demozoo'

DEBUG = False
EMAIL_HOST = 'localhost'

INSTALLED_APPS = list(INSTALLED_APPS) + ['django_gevent_deploy']

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'VHostCallingFormat'

GEVENT_ADDR_PORT = "localhost:4801"

BROKER_URL = 'redis://localhost:6379/0'

ALLOWED_HOSTS = ['localhost', 'demozoo.org', 'matilda.demozoo.org', '46.4.213.51']

USE_PYGAME_IMAGE_CONVERSION = True

# django-compressor offline compression
COMPRESS_OFFLINE = True
COMPRESS_OFFLINE_CONTEXT = {
	'base_template_with_ajax_option': 'base.html',
	'site_is_writeable': True,
}

try:
	from .local import *
except ImportError:
	pass
