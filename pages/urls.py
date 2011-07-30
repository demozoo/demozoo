from django.conf.urls.defaults import *

urlpatterns = patterns('pages.views',
	(r'^(.+)/$', 'page', {}, 'page'),
)
