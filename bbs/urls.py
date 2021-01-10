from django.conf.urls import url

from bbs import views


urlpatterns = [
    url(r'^$', views.index, {}, 'bbses'),
]
