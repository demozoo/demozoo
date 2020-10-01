from .base import *
import os

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#         'NAME': 'demozoo',                      # Or path to database file if using sqlite3.
#         'USER': 'postgres',                      # Not used with sqlite3.
#         'PASSWORD': '',                  # Not used with sqlite3.
#         'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#         'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
#     }
# }

DEBUG = True

BASE_URL = 'http://localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS = list(INSTALLED_APPS) + ['django_extensions']

DEBUG_TOOLBAR_ENABLED = os.getenv('DEBUG_TOOLBAR_ENABLED', '1') != '0'

if DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']
    MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES) + ['debug_toolbar.middleware.DebugToolbarMiddleware']
