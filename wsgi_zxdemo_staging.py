import os
from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'demozoo.settings.zxdemo_staging'
application = get_wsgi_application()
