from .base import *

# DATABASES = {
# 	'default': {
# 		'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
# 		'NAME': 'demozoo',                      # Or path to database file if using sqlite3.
# 		'USER': 'postgres',                      # Not used with sqlite3.
# 		'PASSWORD': '',                  # Not used with sqlite3.
# 		'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
# 		'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
# 	}
# }

DEBUG = True
INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar', 'django_extensions']
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES) + ['debug_toolbar.middleware.DebugToolbarMiddleware']

AWS_QUERYSTRING_AUTH = False
AWS_BOTO_FORCE_HTTP = True
AWS_BOTO_CALLING_FORMAT = 'SubdomainCallingFormat'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
	from .local import *
except ImportError:
	pass
