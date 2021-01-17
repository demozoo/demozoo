from django.conf.urls import url

from bbs import views


urlpatterns = [
    url(r'^$', views.index, {}, 'bbses'),
    url(r'^(\d+)/$', views.show, {}, 'bbs'),
    url(r'^new/$', views.create, {}, 'new_bbs'),
    url(r'^(\d+)/edit/$', views.edit, {}, 'edit_bbs'),
]
