from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from platforms.views import index, show


urlpatterns = [
    url(r'^$', index, {}, 'platforms'),
    url(r'^(\d+)/$', show, {}, 'platform'),
]
