from django.conf.urls import re_path

from bbs import views


urlpatterns = [
    re_path(r'^$', views.index, {}, 'bbses'),
    re_path(r'^tagged/(.+)/$', views.tagged, {}, 'bbses_tagged'),
    re_path(r'^(\d+)/$', views.show, {}, 'bbs'),
    re_path(r'^new/$', views.create, {}, 'new_bbs'),
    re_path(r'^(\d+)/edit/$', views.edit, {}, 'edit_bbs'),
    re_path(r'^(\d+)/edit_notes/$', views.edit_notes, {}, 'bbs_edit_notes'),
    re_path(r'^(\d+)/delete/$', views.DeleteBBSView.as_view(), {}, 'delete_bbs'),
    re_path(r'^(\d+)/edit_bbstros/$', views.edit_bbstros, {}, 'bbs_edit_bbstros'),
    re_path(r'^(\d+)/history/$', views.history, {}, 'bbs_history'),
    re_path(r'^(\d+)/add_operator/$', views.add_operator, {}, 'bbs_add_operator'),
    re_path(r'^(\d+)/edit_operator/(\d+)/$', views.edit_operator, {}, 'bbs_edit_operator'),
    re_path(r'^(\d+)/remove_operator/(\d+)/$', views.RemoveOperatorView.as_view(), {}, 'bbs_remove_operator'),
    re_path(r'^(\d+)/add_affiliation/$', views.add_affiliation, {}, 'bbs_add_affiliation'),
    re_path(r'^(\d+)/edit_affiliation/(\d+)/$', views.edit_affiliation, {}, 'bbs_edit_affiliation'),
    re_path(r'^(\d+)/remove_affiliation/(\d+)/$', views.RemoveAffiliationView.as_view(), {}, 'bbs_remove_affiliation'),
    re_path(r'^(\d+)/edit_text_ads/$', views.EditTextAdsView.as_view(), {}, 'bbs_edit_text_ads'),
    re_path(r'^(\d+)/text_ad/(\d+)/$', views.text_ad, {}, 'bbs_text_ad'),
    re_path(r'^(\d+)/edit_tags/$', views.BBSEditTagsView.as_view(), {}, 'bbs_edit_tags'),
    re_path(r'^(\d+)/add_tag/$', views.BBSAddTagView.as_view(), {}, 'bbs_add_tag'),
    re_path(r'^(\d+)/remove_tag/$', views.BBSRemoveTagView.as_view(), {}, 'bbs_remove_tag'),
    re_path(r'^(\d+)/edit_external_links/$', views.edit_external_links, {}, 'bbs_edit_external_links'),
]
