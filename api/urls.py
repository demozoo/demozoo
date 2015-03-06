from django.conf.urls import patterns, url, include

from rest_framework import routers
from api.views import generic

router = routers.DefaultRouter()
router.register(r'productions', generic.ProductionViewSet)
router.register(r'releasers', generic.ReleaserViewSet)
router.register(r'platforms', generic.PlatformViewSet)


urlpatterns = patterns('api.views',
	(r'^adhoc/pouet-credits/$', 'adhoc.pouet.credits', {}),
	(r'^adhoc/pouet/prod-demozoo-ids-by-pouet-id/$', 'adhoc.pouet.prod_demozoo_ids_by_pouet_id', {}),
	(r'^adhoc/pouet/group-demozoo-ids-by-pouet-id/$', 'adhoc.pouet.group_demozoo_ids_by_pouet_id', {}),
	(r'^adhoc/pouet/party-demozoo-ids-by-pouet-id/$', 'adhoc.pouet.party_demozoo_ids_by_pouet_id', {}),

	(r'^adhoc/zxdemo/prod-demozoo-ids-by-zxdemo-id/$', 'adhoc.zxdemo.prod_demozoo_ids_by_zxdemo_id', {}),
	(r'^adhoc/zxdemo/group-demozoo-ids-by-zxdemo-id/$', 'adhoc.zxdemo.group_demozoo_ids_by_zxdemo_id', {}),
	(r'^adhoc/zxdemo/party-demozoo-ids-by-zxdemo-id/$', 'adhoc.zxdemo.party_demozoo_ids_by_zxdemo_id', {}),

	(r'^adhoc/klubi/demoshow-prods/$', 'adhoc.klubi.demoshow', {}),
	(r'^adhoc/scenesat/monthly-releases/$', 'adhoc.scenesat.monthly', {}),
)

urlpatterns += [
	url(r'^v1/', include(router.urls)),
]
