from django.conf.urls import url

from forums import views as forums_views

urlpatterns = [
    url(r'^$', forums_views.index, {}, 'forums'),
    url(r'^new/$', forums_views.new_topic, {}, 'forums_new_topic'),
    url(r'^(\d+)/$', forums_views.topic, {}, 'forums_topic'),
    url(r'^post/(\d+)/$', forums_views.post, {}, 'forums_post'),
    url(r'^(\d+)/reply/$', forums_views.topic_reply, {}, 'forums_topic_reply'),
]
