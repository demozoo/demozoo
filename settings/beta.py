from .base import *

DATABASES['default']['NAME'] = 'demozoobeta'
DATABASES['default']['USER'] = 'demozoo'

DATABASES['geonameslite']['USER'] = 'demozoo'

DEBUG = False
EMAIL_HOST = 'localhost'

INSTALLED_APPS = list(INSTALLED_APPS) + ['django_gevent_deploy']

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'SubdomainCallingFormat'

GEVENT_ADDR_PORT = "localhost:4820"

ALLOWED_HOSTS = ['beta.demozoo.org']

USE_PYGAME_IMAGE_CONVERSION = True

try:
	from .local import *
except ImportError:
	pass
