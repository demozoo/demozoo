from django.urls import path

from search import views as search_views


urlpatterns = [
    path("", search_views.search, {}, "search"),
    path("live/", search_views.live_search, {}, "live_search"),
]
