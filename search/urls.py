from django.conf.urls import patterns

urlpatterns = patterns('search.views',
	(r'^$', 'search', {}, 'search'),
	(r'^live/$', 'live_search', {}, 'live_search'),
)
