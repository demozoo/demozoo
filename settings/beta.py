from .base import *

DATABASES['default']['NAME'] = 'demozoobeta'
DATABASES['default']['USER'] = 'demozoo'

DATABASES['geonameslite']['USER'] = 'demozoo'

DEBUG = False
EMAIL_HOST = 'localhost'

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'SubdomainCallingFormat'

ALLOWED_HOSTS = ['beta.demozoo.org', 'localhost']

USE_PYGAME_IMAGE_CONVERSION = True

try:
	from .local import *
except ImportError:
	pass
