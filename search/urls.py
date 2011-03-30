from django.conf.urls.defaults import *

urlpatterns = patterns('search.views',
	(r'^$', 'search', {}, 'search'),
)
