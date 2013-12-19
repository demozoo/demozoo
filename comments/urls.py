from django.conf.urls import *

urlpatterns = patterns('comments.views',
	(r'^productions/(\d+)/comments/new/$', 'add_production_comment', {}, 'add_production_comment'),
	(r'^productions/(\d+)/comments/(\d+)/edit/$', 'edit_production_comment', {}, 'edit_production_comment'),
)
