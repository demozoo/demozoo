from django.conf.urls import patterns

urlpatterns = patterns('api.views',
	(r'^adhoc/pouet-credits/$', 'adhoc.pouet.credits', {}),
	(r'^adhoc/pouet/prod-demozoo-ids-by-pouet-id/$', 'adhoc.pouet.prod_demozoo_ids_by_pouet_id', {}),
	(r'^adhoc/pouet/prod-demozoo-ids-by-zxdemo-id/$', 'adhoc.pouet.prod_demozoo_ids_by_zxdemo_id', {}),
	(r'^adhoc/pouet/group-demozoo-ids-by-pouet-id/$', 'adhoc.pouet.group_demozoo_ids_by_pouet_id', {}),
	(r'^adhoc/pouet/group-demozoo-ids-by-zxdemo-id/$', 'adhoc.pouet.group_demozoo_ids_by_zxdemo_id', {}),

	(r'^adhoc/klubi/demoshow-prods/$', 'adhoc.klubi.demoshow', {}),
	(r'^adhoc/scenesat/monthly-releases/$', 'adhoc.scenesat.monthly', {}),
)
