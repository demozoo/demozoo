import os
import sys
import site
site.addsitedir('/home/demozoo/virtualenv/lib/python2.6/site-packages')

sys.path.append('/var/www/demozoo2/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
