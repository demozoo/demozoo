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

try:
	from .local import *
except ImportError:
	pass
