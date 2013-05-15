from .base import *

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
		'NAME': 'demozoo',                      # Or path to database file if using sqlite3.
		'USER': 'demozoo',                      # Not used with sqlite3.
		'PASSWORD': '',                  # Not used with sqlite3.
		'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
		'PORT': '4800',                      # Set to empty string for default. Not used with sqlite3.
	}
}

DEBUG = False
EMAIL_HOST = 'localhost'

INSTALLED_APPS = list(INSTALLED_APPS) + ['django_gevent_deploy']

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'VHostCallingFormat'

GEVENT_ADDR_PORT = "localhost:4801"

try:
	from .local import *
except ImportError:
	pass
