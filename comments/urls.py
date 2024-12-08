from django.urls import path

from comments import views


urlpatterns = [
    path(
        "productions/<int:production_id>/comments/new/",
        views.AddProductionCommentView.as_view(),
        name="add_production_comment",
    ),
    path(
        "productions/<int:production_id>/comments/<int:comment_id>/edit/",
        views.EditProductionCommentView.as_view(),
        name="edit_production_comment",
    ),
    path(
        "productions/<int:production_id>/comments/<int:comment_id>/delete/",
        views.DeleteProductionCommentView.as_view(),
        name="delete_production_comment",
    ),
    path("parties/<int:party_id>/comments/new/", views.AddPartyCommentView.as_view(), name="add_party_comment"),
    path(
        "parties/<int:party_id>/comments/<int:comment_id>/edit/",
        views.EditPartyCommentView.as_view(),
        name="edit_party_comment",
    ),
    path(
        "parties/<int:party_id>/comments/<int:comment_id>/delete/",
        views.DeletePartyCommentView.as_view(),
        name="delete_party_comment",
    ),
    path("bbs/<int:bbs_id>/comments/new/", views.AddBBSCommentView.as_view(), name="add_bbs_comment"),
    path(
        "bbs/<int:bbs_id>/comments/<int:comment_id>/edit/", views.EditBBSCommentView.as_view(), name="edit_bbs_comment"
    ),
    path(
        "bbs/<int:bbs_id>/comments/<int:comment_id>/delete/",
        views.DeleteBBSCommentView.as_view(),
        name="delete_bbs_comment",
    ),
]
