from django.conf.urls import *

urlpatterns = patterns('search.views',
	(r'^$', 'search', {}, 'search'),
)
