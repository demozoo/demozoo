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

ALLOWED_HOSTS = ['localhost', 'demozoo.org', '46.4.213.51']

try:
	from .local import *
except ImportError:
	pass
