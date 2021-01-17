from django.conf.urls import url

from bbs import views


urlpatterns = [
    url(r'^$', views.index, {}, 'bbses'),
    url(r'^(\d+)/$', views.show, {}, 'bbs'),
    url(r'^new/$', views.create, {}, 'new_bbs'),
    url(r'^(\d+)/edit/$', views.edit, {}, 'edit_bbs'),
    url(r'^(\d+)/edit_notes/$', views.edit_notes, {}, 'bbs_edit_notes'),
    url(r'^(\d+)/delete/$', views.delete, {}, 'delete_bbs'),
    url(r'^(\d+)/edit_bbstros/$', views.edit_bbstros, {}, 'bbs_edit_bbstros'),
    url(r'^(\d+)/history/$', views.history, {}, 'bbs_history'),
    url(r'^(\d+)/add_operator/$', views.add_operator, {}, 'bbs_add_operator'),
]
