from django.conf.urls import *

urlpatterns = patterns('pages.views',
	(r'^(.+)/$', 'page', {}, 'page'),
)
