# Django settings for demozoo2 project.

# Determine paths
import os
import sys
FILEROOT = os.path.join(os.path.dirname(__file__), '..')

# Modify sys.path so it contains the right things
sys.path.append(FILEROOT)
sys.path.append(os.path.join(FILEROOT, "lib"))

TEMPLATE_DEBUG = True

ADMINS = (
	('Matt Westcott', 'matt@west.co.tt'),
)
SERVER_EMAIL = 'matt@west.co.tt'
EMAIL_SUBJECT_PREFIX = '[Demozoo] '

MANAGERS = ADMINS

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
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
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

STATIC_ROOT = os.path.join(FILEROOT, "static")
STATIC_URL = "/static/"
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
	# other finders..
	'compressor.finders.CompressorFinder',
)

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
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
	'django.contrib.staticfiles',
	'south',
	'djapian',
	'treebeard',
	'taggit',
	'compressor',
	'djcelery',
	'django_bcrypt',

	'demoscene',
	'search',
	'dataexchange',
	'maintenance',
	'pages',
	'sceneorg',
	'mirror',
	'screenshots',
	'homepage',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += (
	'django.core.context_processors.request',
	'demoscene.context_processors.global_nav_forms',
	'demoscene.context_processors.ajax_base_template',
	'demoscene.context_processors.read_only_mode',
)

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'filters': {
		'require_debug_false': {
			'()': 'django.utils.log.RequireDebugFalse'
		}
	},
	'handlers': {
		'mail_admins': {
			'level': 'ERROR',
			'filters': ['require_debug_false'],
			'class': 'django.utils.log.AdminEmailHandler'
		}
	},
	'loggers': {
		'django.request': {
			'handlers': ['mail_admins'],
			'level': 'ERROR',
			'propagate': True,
		},
	}
}

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'

DJAPIAN_DATABASE_PATH = os.path.join(FILEROOT, 'data', 'djapian')

DEFAULT_FILE_STORAGE = 's3boto.S3BotoStorage'

AUTH_PROFILE_MODULE = 'demoscene.AccountProfile'

INTERNAL_IPS = ('127.0.0.1',)

# COMPRESS_ENABLED = False # enable JS/CSS asset packaging/compression
COMPRESS_URL = '/static/'
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_PRECOMPILERS = (
	('text/less', 'lessc {infile} {outfile}'),
)

# Celery settings
import djcelery
djcelery.setup_loader()
BROKER_URL = 'redis://localhost:6379/0'
CELERY_ROUTES = {
	'screenshots.tasks.create_screenshot_versions_from_local_file': {'queue': 'fasttrack'},
}
CELERYD_CONCURRENCY = 2

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
	"fetch-new-sceneorg-files": {
		"task": "sceneorg.tasks.fetch_sceneorg_dir",
		"schedule": timedelta(hours=4),
		"args": ('/', 1)
	},
	"fetch-all-sceneorg-files": {
		"task": "sceneorg.tasks.scan_dir_listing",
		"schedule": timedelta(days=8),
		"args": ()
	},
	"set-default-screenshots": {
		"task": "demoscene.tasks.set_default_screenshots",
		"schedule": timedelta(hours=1),
		"args": ()
	},
}

# Read-only mode
SITE_IS_WRITEABLE = True
