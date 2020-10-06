from __future__ import absolute_import, unicode_literals

import os

import dotenv
from django.core.wsgi import get_wsgi_application

dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'demozoo.settings.zxdemo_productionvm'
application = get_wsgi_application()
