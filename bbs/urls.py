from django.conf.urls import url

from bbs import views


urlpatterns = [
    url(r'^$', views.index, {}, 'bbses'),
    url(r'^(\d+)/$', views.show, {}, 'bbs'),
    url(r'^new/$', views.create, {}, 'new_bbs'),
    url(r'^(\d+)/edit/$', views.edit, {}, 'edit_bbs'),
    url(r'^(\d+)/edit_notes/$', views.edit_notes, {}, 'bbs_edit_notes'),
    url(r'^(\d+)/delete/$', views.DeleteBBSView.as_view(), {}, 'delete_bbs'),
    url(r'^(\d+)/edit_bbstros/$', views.edit_bbstros, {}, 'bbs_edit_bbstros'),
    url(r'^(\d+)/history/$', views.history, {}, 'bbs_history'),
    url(r'^(\d+)/add_operator/$', views.add_operator, {}, 'bbs_add_operator'),
    url(r'^(\d+)/edit_operator/(\d+)/$', views.edit_operator, {}, 'bbs_edit_operator'),
    url(r'^(\d+)/remove_operator/(\d+)/$', views.RemoveOperatorView.as_view(), {}, 'bbs_remove_operator'),
    url(r'^(\d+)/add_affiliation/$', views.add_affiliation, {}, 'bbs_add_affiliation'),
    url(r'^(\d+)/edit_affiliation/(\d+)/$', views.edit_affiliation, {}, 'bbs_edit_affiliation'),
    url(r'^(\d+)/remove_affiliation/(\d+)/$', views.RemoveAffiliationView.as_view(), {}, 'bbs_remove_affiliation'),
    url(r'^(\d+)/edit_text_ads/$', views.EditTextAdsView.as_view(), {}, 'bbs_edit_text_ads'),
    url(r'^(\d+)/text_ad/(\d+)/$', views.text_ad, {}, 'bbs_text_ad'),
]
