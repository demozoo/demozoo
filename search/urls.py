from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from search import views as search_views


urlpatterns = [
    url(r'^$', search_views.search, {}, 'search'),
    url(r'^live/$', search_views.live_search, {}, 'live_search'),
]
