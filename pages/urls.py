from django.conf.urls import patterns

urlpatterns = patterns('pages.views',
	(r'^(.+)/$', 'page', {}, 'page'),
)
