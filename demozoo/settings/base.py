# Determine paths
import os
import sys
from datetime import timedelta


# Django settings for demozoo2 project.

FILEROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

# Modify sys.path so it contains the right things
sys.path.append(FILEROOT)
sys.path.append(os.path.join(FILEROOT, "lib"))

# subsite: 'demozoo' or 'zxdemo'. Varies root_urlconf and context processors
SUBSITE = os.getenv('DEMOZOO_SUBSITE', 'demozoo')

ADMINS = (
    ('Matt Westcott', 'matt@west.co.tt'),
)
SERVER_EMAIL = 'matt@west.co.tt'
EMAIL_SUBJECT_PREFIX = '[Demozoo] '
DEFAULT_FROM_EMAIL = 'matt@west.co.tt'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('POSTGRES_DB_NAME', 'demozoo'),
        'USER': os.getenv('POSTGRES_USER', 'demozoo'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', ''),  # Set to empty string for localhost.
        'PORT': os.getenv('POSTGRES_PORT', ''),  # Set to empty string for default.
        'CONN_MAX_AGE': 600,  # number of seconds database connections should persist for
    }
}

SECRET_KEY = os.getenv('SECRET_KEY')

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
STATICFILES_DIRS = [
    os.path.join(FILEROOT, 'static_built'),
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

CONTEXT_PROCESSORS = [
    # defaults
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.i18n',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    # added by us
    'django.template.context_processors.request',
]

if SUBSITE == 'zxdemo':
    CONTEXT_PROCESSORS += [
        'zxdemo.context_processors.zxdemo_context',
    ]
else:
    CONTEXT_PROCESSORS += [
        'demoscene.context_processors.global_nav_forms',
        'demoscene.context_processors.ajax_base_template',
        'demoscene.context_processors.read_only_mode',
    ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(FILEROOT, 'demozoo', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
        },
    },
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

if SUBSITE == 'zxdemo':
    ROOT_URLCONF = 'zxdemo.urls'
else:
    ROOT_URLCONF = 'demozoo.urls'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'treebeard',
    'taggit',
    'compressor',
    'rest_framework',
    'corsheaders',

    'demoscene',
    'parties',
    'platforms',
    'productions',
    'search',
    'maintenance',
    'pages',
    'sceneorg',
    'pouet',
    'mirror',
    'screenshots',
    'homepage',
    'comments',
    'forums',
    'zxdemo',
    'users',
    'janeway',
    'awards',
    'bbs',
]

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

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# yes, I like my Django storage backends to follow the motherfucking spec and not silently overwrite files, THANKS
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = 'public-read'

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_SECURE_URLS = os.getenv('AWS_S3_SECURE_URLS', '1') != '0'

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')


AUTH_PROFILE_MODULE = 'demoscene.AccountProfile'

INTERNAL_IPS = ('127.0.0.1',)

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# COMPRESS_ENABLED = False # enable JS/CSS asset packaging/compression
COMPRESS_URL = '/static/'
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_PRECOMPILERS = (
    # ('text/less', 'lessc --glob --autoprefix="last 2 versions" --clean-css="--s1 --advanced" {infile} {outfile}'),
)

REDIS_URL = 'redis://localhost:6379/0'

# Celery settings
BROKER_URL = REDIS_URL
CELERY_ROUTES = {
    'screenshots.tasks.create_screenshot_versions_from_local_file': {'queue': 'fasttrack'},
    'productions.tasks.fetch_production_link_embed_data': {'queue': 'fasttrack'},
}
CELERYD_CONCURRENCY = 2
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']


CELERYBEAT_SCHEDULE = {
    "fetch-new-sceneorg-files": {
        "task": "sceneorg.tasks.fetch_new_sceneorg_files",
        "schedule": timedelta(hours=1),
        "args": (1,)
    },
    "fetch-all-sceneorg-files": {
        "task": "sceneorg.tasks.scan_dir_listing",
        "schedule": timedelta(days=8),
        "args": ()
    },
    "fetch-remote-screenshots": {
        "task": "screenshots.tasks.fetch_remote_screenshots",
        "schedule": timedelta(days=1),
        "args": ()
    },
    # "automatch-janeway-authors": {
    #     "task": "janeway.tasks.automatch_all_authors",
    #     "schedule": timedelta(days=1),
    #     "args": ()
    # }
}

MEDIA_ROOT = os.path.join(FILEROOT, 'media')

REST_FRAMEWORK = {
    # do not support any authentication mechanism; anonymous read-only access only.
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_jsonp.renderers.JSONPRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

AUTHENTICATION_BACKENDS = (
    'sceneid.backends.SceneIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

BASE_URL = 'https://demozoo.org'
HTTP_USER_AGENT = 'Demozoo/2.0 (gasman@raww.org; http://demozoo.org/)'

GEOCODER_URL = 'http://geocoder.demozoo.org/'
SCENEID_HOST = 'https://id.scene.org/'

SCENEID_KEY = os.getenv('SCENEID_KEY')
SCENEID_SECRET = os.getenv('SCENEID_SECRET')

CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r'^/api/v1/.*$'
CORS_ALLOW_METHODS = ['GET']

# Read-only mode
SITE_IS_WRITEABLE = os.getenv('SITE_IS_WRITEABLE', '1') != '0'
