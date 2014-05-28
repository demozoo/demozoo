from django.conf.urls import url

from comments.views import AddProductionCommentView, EditProductionCommentView, DeleteProductionCommentView

urlpatterns = [
	url(r'^productions/(\d+)/comments/new/$', AddProductionCommentView.as_view(), name='add_production_comment'),
	url(r'^productions/(\d+)/comments/(\d+)/edit/$', EditProductionCommentView.as_view(), name='edit_production_comment'),
	url(r'^productions/(\d+)/comments/(\d+)/delete/$', DeleteProductionCommentView.as_view(), name='delete_production_comment'),
]
