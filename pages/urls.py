from django.conf.urls import re_path

from pages import views as pages_views


urlpatterns = [
    re_path(r'^(.+)/$', pages_views.page, {}, 'page'),
]
