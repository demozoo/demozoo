from django.conf.urls import patterns

urlpatterns = patterns('api.views',
	(r'^adhoc/pouet-credits/$', 'adhoc.pouet.credits', {}),
	(r'^adhoc/klubi/demoshow-prods/$', 'adhoc.klubi.demoshow', {}),
	(r'^adhoc/scenesat/monthly-releases/$', 'adhoc.scenesat.monthly', {}),
)
