from django.conf.urls import patterns

urlpatterns = patterns('api.views',
	(r'^adhoc/pouet-credits/$', 'adhoc.pouet_credits', {}),
	(r'^adhoc/klubi/demoshow-prods/$', 'adhoc.klubi_demoshow', {}),
	(r'^adhoc/scenesat/monthly-releases/$', 'adhoc.scenesat_monthly', {}),
)
