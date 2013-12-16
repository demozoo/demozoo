from django.conf.urls import *

urlpatterns = patterns('comments.views',
	(r'^productions/(\d+)/comments/new/$', 'add_production_comment', {}, 'add_production_comment'),
)
