from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.views.generic import RedirectView

from users.views import show, index

urlpatterns = [
    url(r'^$', index, {}, 'users_index'),
    url(r'^(\d+)/$', show, {}, 'user'),
]
