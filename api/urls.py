from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from rest_framework import routers

from api.views import adhoc, generic

router = routers.DefaultRouter()
router.register(r'productions', generic.ProductionViewSet)
router.register(r'production_types', generic.ProductionTypeViewSet)
router.register(r'releasers', generic.ReleaserViewSet)
router.register(r'platforms', generic.PlatformViewSet)
router.register(r'party_series', generic.PartySeriesViewSet)
router.register(r'parties', generic.PartyViewSet)


urlpatterns = [
    url(r'^adhoc/pouet-credits/$', adhoc.pouet.credits, {}),
    url(r'^adhoc/pouet/prod-demozoo-ids-by-pouet-id/$', adhoc.pouet.prod_demozoo_ids_by_pouet_id, {}),
    url(r'^adhoc/pouet/group-demozoo-ids-by-pouet-id/$', adhoc.pouet.group_demozoo_ids_by_pouet_id, {}),
    url(r'^adhoc/pouet/party-demozoo-ids-by-pouet-id/$', adhoc.pouet.party_demozoo_ids_by_pouet_id, {}),

    url(r'^adhoc/zxdemo/prod-demozoo-ids-by-zxdemo-id/$', adhoc.zxdemo.prod_demozoo_ids_by_zxdemo_id, {}),
    url(r'^adhoc/zxdemo/group-demozoo-ids-by-zxdemo-id/$', adhoc.zxdemo.group_demozoo_ids_by_zxdemo_id, {}),
    url(r'^adhoc/zxdemo/party-demozoo-ids-by-zxdemo-id/$', adhoc.zxdemo.party_demozoo_ids_by_zxdemo_id, {}),

    url(r'^adhoc/klubi/demoshow-prods/$', adhoc.klubi.demoshow, {}),
    url(r'^adhoc/scenesat/monthly-releases/$', adhoc.scenesat.monthly, {}),

    url(r'^adhoc/eq/demos/$', adhoc.eq.demos, {}),
    url(r'^adhoc/group-abbreviations/$', adhoc.group_abbreviations.group_abbreviations, {}),

    url(r'^v1/', include(router.urls)),
]
