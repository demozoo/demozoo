from django.conf.urls import url

from comments import views

urlpatterns = [
    url(r'^productions/(\d+)/comments/new/$', views.AddProductionCommentView.as_view(), name='add_production_comment'),
    url(r'^productions/(\d+)/comments/(\d+)/edit/$', views.EditProductionCommentView.as_view(), name='edit_production_comment'),
    url(r'^productions/(\d+)/comments/(\d+)/delete/$', views.DeleteProductionCommentView.as_view(), name='delete_production_comment'),

    url(r'^parties/(\d+)/comments/new/$', views.AddPartyCommentView.as_view(), name='add_party_comment'),
    url(r'^parties/(\d+)/comments/(\d+)/edit/$', views.EditPartyCommentView.as_view(), name='edit_party_comment'),
    url(r'^parties/(\d+)/comments/(\d+)/delete/$', views.DeletePartyCommentView.as_view(), name='delete_party_comment'),
]
