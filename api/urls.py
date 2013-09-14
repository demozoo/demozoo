from django.conf.urls import *

urlpatterns = patterns('api.views',
	(r'^adhoc/pouet-credits/$', 'adhoc.pouet_credits', {}),
)
