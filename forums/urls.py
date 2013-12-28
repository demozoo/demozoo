from django.conf.urls import *

urlpatterns = patterns('forums.views',
	(r'^$', 'index', {}, 'forums'),
	(r'^new/$', 'new_topic', {}, 'forums_new_topic'),
	(r'^(\d+)/$', 'topic', {}, 'forums_topic'),
)
