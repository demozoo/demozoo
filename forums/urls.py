from django.conf.urls import patterns

urlpatterns = patterns('forums.views',
	(r'^$', 'index', {}, 'forums'),
	(r'^new/$', 'new_topic', {}, 'forums_new_topic'),
	(r'^(\d+)/$', 'topic', {}, 'forums_topic'),
	(r'^post/(\d+)/$', 'post', {}, 'forums_post'),
	(r'^(\d+)/reply/$', 'topic_reply', {}, 'forums_topic_reply'),
)
