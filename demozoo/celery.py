from __future__ import absolute_import

import os

import dotenv
from celery import Celery


env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), '.env')
dotenv.read_dotenv(env_file)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demozoo.settings.dev')

from django.conf import settings


app = Celery('demozoo')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
