from django.conf.urls import re_path

from comments import views


urlpatterns = [
    re_path(
        r'^productions/(\d+)/comments/new/$', views.AddProductionCommentView.as_view(),
        name='add_production_comment'
    ),
    re_path(
        r'^productions/(\d+)/comments/(\d+)/edit/$', views.EditProductionCommentView.as_view(),
        name='edit_production_comment'
    ),
    re_path(
        r'^productions/(\d+)/comments/(\d+)/delete/$', views.DeleteProductionCommentView.as_view(),
        name='delete_production_comment'
    ),

    re_path(
        r'^parties/(\d+)/comments/new/$', views.AddPartyCommentView.as_view(),
        name='add_party_comment'
    ),
    re_path(
        r'^parties/(\d+)/comments/(\d+)/edit/$', views.EditPartyCommentView.as_view(),
        name='edit_party_comment'
    ),
    re_path(
        r'^parties/(\d+)/comments/(\d+)/delete/$', views.DeletePartyCommentView.as_view(),
        name='delete_party_comment'
    ),
]
