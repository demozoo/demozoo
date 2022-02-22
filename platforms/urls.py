from django.conf.urls import re_path

from platforms.views import index, show


urlpatterns = [
    re_path(r'^$', index, {}, 'platforms'),
    re_path(r'^(\d+)/$', show, {}, 'platform'),
]
