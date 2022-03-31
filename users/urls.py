from django.urls import re_path

from users.views import index, show


urlpatterns = [
    re_path(r'^$', index, {}, 'users_index'),
    re_path(r'^(\d+)/$', show, {}, 'user'),
]
