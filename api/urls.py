from django.urls import include, re_path
from rest_framework import routers

from api.views import generic
from api.views.adhoc import eq, group_abbreviations, klubi, pouet, scenesat, zxdemo


router = routers.DefaultRouter()
router.register(r'productions', generic.ProductionViewSet)
router.register(r'production_types', generic.ProductionTypeViewSet)
router.register(r'releasers', generic.ReleaserViewSet)
router.register(r'platforms', generic.PlatformViewSet)
router.register(r'party_series', generic.PartySeriesViewSet)
router.register(r'parties', generic.PartyViewSet)
router.register(r'bbses', generic.BBSViewSet)


urlpatterns = [
    re_path(r'^adhoc/pouet-credits/$', pouet.credits, {}),
    re_path(r'^adhoc/pouet/prod-demozoo-ids-by-pouet-id/$', pouet.prod_demozoo_ids_by_pouet_id, {}),
    re_path(r'^adhoc/pouet/group-demozoo-ids-by-pouet-id/$', pouet.group_demozoo_ids_by_pouet_id, {}),
    re_path(r'^adhoc/pouet/party-demozoo-ids-by-pouet-id/$', pouet.party_demozoo_ids_by_pouet_id, {}),

    re_path(r'^adhoc/zxdemo/prod-demozoo-ids-by-zxdemo-id/$', zxdemo.prod_demozoo_ids_by_zxdemo_id, {}),
    re_path(r'^adhoc/zxdemo/group-demozoo-ids-by-zxdemo-id/$', zxdemo.group_demozoo_ids_by_zxdemo_id, {}),
    re_path(r'^adhoc/zxdemo/party-demozoo-ids-by-zxdemo-id/$', zxdemo.party_demozoo_ids_by_zxdemo_id, {}),

    re_path(r'^adhoc/klubi/demoshow-prods/$', klubi.demoshow, {}),
    re_path(r'^adhoc/scenesat/monthly-releases/$', scenesat.monthly, {}),

    re_path(r'^adhoc/eq/demos/$', eq.demos, {}),
    re_path(r'^adhoc/group-abbreviations/$', group_abbreviations.group_abbreviations, {}),

    re_path(r'^v1/', include(router.urls)),
]
