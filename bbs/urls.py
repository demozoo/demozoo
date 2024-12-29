from django.urls import path

from bbs import views


urlpatterns = [
    path("", views.index, {}, "bbses"),
    path("tagged/<str:tag_name>/", views.tagged, {}, "bbses_tagged"),
    path("<int:bbs_id>/", views.show, {}, "bbs"),
    path("new/", views.CreateView.as_view(), {}, "new_bbs"),
    path("<int:bbs_id>/edit/", views.EditView.as_view(), {}, "edit_bbs"),
    path("<int:bbs_id>/edit_notes/", views.EditNotesView.as_view(), {}, "bbs_edit_notes"),
    path("<int:bbs_id>/delete/", views.DeleteBBSView.as_view(), {}, "delete_bbs"),
    path("<int:bbs_id>/edit_bbstros/", views.EditBBStrosView.as_view(), {}, "bbs_edit_bbstros"),
    path("<int:bbs_id>/history/", views.history, {}, "bbs_history"),
    path("<int:bbs_id>/add_operator/", views.AddOperatorView.as_view(), {}, "bbs_add_operator"),
    path("<int:bbs_id>/edit_operator/<int:operator_id>/", views.edit_operator, {}, "bbs_edit_operator"),
    path(
        "<int:bbs_id>/remove_operator/<int:operator_id>/", views.RemoveOperatorView.as_view(), {}, "bbs_remove_operator"
    ),
    path("<int:bbs_id>/add_affiliation/", views.add_affiliation, {}, "bbs_add_affiliation"),
    path("<int:bbs_id>/edit_affiliation/<int:affiliation_id>/", views.edit_affiliation, {}, "bbs_edit_affiliation"),
    path(
        "<int:bbs_id>/remove_affiliation/<int:affiliation_id>/",
        views.RemoveAffiliationView.as_view(),
        {},
        "bbs_remove_affiliation",
    ),
    path("<int:bbs_id>/edit_text_ads/", views.EditTextAdsView.as_view(), {}, "bbs_edit_text_ads"),
    path("<int:bbs_id>/text_ad/<int:file_id>/", views.text_ad, {}, "bbs_text_ad"),
    path("<int:bbs_id>/edit_tags/", views.BBSEditTagsView.as_view(), {}, "bbs_edit_tags"),
    path("<int:bbs_id>/add_tag/", views.BBSAddTagView.as_view(), {}, "bbs_add_tag"),
    path("<int:bbs_id>/remove_tag/", views.BBSRemoveTagView.as_view(), {}, "bbs_remove_tag"),
    path("<int:bbs_id>/edit_external_links/", views.edit_external_links, {}, "bbs_edit_external_links"),
]
