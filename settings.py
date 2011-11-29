# Django settings for demozoo2 project.

# Determine paths
import os, sys
FILEROOT = os.path.dirname(__file__)
STATICROOT = os.path.join(FILEROOT, "static")

# Modify sys.path so it contains the right things
sys.path.append(FILEROOT)
sys.path.append(os.path.join(FILEROOT, "lib"))
sys.path.insert(0, os.path.join(FILEROOT, "lib", "south"))

TEMPLATE_DEBUG = True

ADMINS = (
	('Matt Westcott', 'matt@west.co.tt'),
)
SERVER_EMAIL = 'matt@west.co.tt'
EMAIL_SUBJECT_PREFIX = '[Demozoo] '

MANAGERS = ADMINS

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
		'NAME': 'demozoo',                      # Or path to database file if using sqlite3.
		'USER': 'postgres',                      # Not used with sqlite3.
		'PASSWORD': '',                  # Not used with sqlite3.
		'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
		'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
	}
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(STATICROOT, "uploads")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/uploads/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'debug_toolbar.middleware.DebugToolbarMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	os.path.join(FILEROOT, 'templates'),
)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.messages',
	'django.contrib.admin',
	'django.contrib.humanize',
	'south',
	'djapian',
	'treebeard',
	'taggit',
	'debug_toolbar',
	'unjoinify',
	'compressor',
	'djcelery',
	
	'demoscene',
	'search',
	'dataexchange',
	'maintenance',
	'pages',
	'sceneorg',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
	'django.core.context_processors.request',
	'demoscene.context_processors.jquery_include_context_processor',
	'demoscene.context_processors.global_search_form',
) 

LOGIN_REDIRECT_URL = '/'

DJAPIAN_DATABASE_PATH = os.path.join(FILEROOT,'data','djapian')

DEFAULT_FILE_STORAGE = 's3boto.S3BotoStorage'

AUTH_PROFILE_MODULE = 'demoscene.AccountProfile'

INTERNAL_IPS = ('127.0.0.1',)

# COMPRESS_ENABLED = False # enable JS/CSS asset packaging/compression
COMPRESS_URL = '/static/'
COMPRESS_ROOT = STATICROOT

# Celery settings
import djcelery
djcelery.setup_loader()
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"

# Get local settings
try:
	from local_settings import *
except ImportError:
	print "You have no local_settings.py file! Run:   cp local_settings.py.example local_settings.py"
	sys.exit(1)
