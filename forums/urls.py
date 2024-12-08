from django.urls import path

from forums import views as forums_views


urlpatterns = [
    path("", forums_views.index, {}, "forums"),
    path("new/", forums_views.new_topic, {}, "forums_new_topic"),
    path("<int:topic_id>/", forums_views.topic, {}, "forums_topic"),
    path("post/<int:post_id>/", forums_views.post, {}, "forums_post"),
    path("post/<int:post_id>/delete/", forums_views.DeletePostView.as_view(), {}, "forums_delete_post"),
    path("post/<int:post_id>/edit/", forums_views.EditPostView.as_view(), {}, "forums_edit_post"),
    path("<int:topic_id>/reply/", forums_views.topic_reply, {}, "forums_topic_reply"),
]
