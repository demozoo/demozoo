from django.urls import re_path

from search import views as search_views


urlpatterns = [
    re_path(r'^$', search_views.search, {}, 'search'),
    re_path(r'^live/$', search_views.live_search, {}, 'live_search'),
]
