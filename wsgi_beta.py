import os
import django.core.handlers.wsgi
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.beta'
application = django.core.handlers.wsgi.WSGIHandler()
