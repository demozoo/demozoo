from django.conf.urls import re_path

from forums import views as forums_views


urlpatterns = [
    re_path(r'^$', forums_views.index, {}, 'forums'),
    re_path(r'^new/$', forums_views.new_topic, {}, 'forums_new_topic'),
    re_path(r'^(\d+)/$', forums_views.topic, {}, 'forums_topic'),
    re_path(r'^post/(\d+)/$', forums_views.post, {}, 'forums_post'),
    re_path(r'^(\d+)/reply/$', forums_views.topic_reply, {}, 'forums_topic_reply'),
]
