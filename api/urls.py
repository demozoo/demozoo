from django.urls import include, path
from rest_framework import routers

from api.views import generic
from api.views.adhoc import eq, group_abbreviations, klubi, meteoriks, pouet, scenesat, zxdemo


router = routers.DefaultRouter()
router.register("productions", generic.ProductionViewSet)
router.register("production_types", generic.ProductionTypeViewSet)
router.register("releasers", generic.ReleaserViewSet)
router.register("platforms", generic.PlatformViewSet)
router.register("party_series", generic.PartySeriesViewSet)
router.register("parties", generic.PartyViewSet)
router.register("bbses", generic.BBSViewSet)


urlpatterns = [
    path("adhoc/pouet-credits/", pouet.credits, {}),
    path("adhoc/pouet/prod-demozoo-ids-by-pouet-id/", pouet.prod_demozoo_ids_by_pouet_id, {}),
    path("adhoc/pouet/group-demozoo-ids-by-pouet-id/", pouet.group_demozoo_ids_by_pouet_id, {}),
    path("adhoc/pouet/party-demozoo-ids-by-pouet-id/", pouet.party_demozoo_ids_by_pouet_id, {}),
    path("adhoc/zxdemo/prod-demozoo-ids-by-zxdemo-id/", zxdemo.prod_demozoo_ids_by_zxdemo_id, {}),
    path("adhoc/zxdemo/group-demozoo-ids-by-zxdemo-id/", zxdemo.group_demozoo_ids_by_zxdemo_id, {}),
    path("adhoc/zxdemo/party-demozoo-ids-by-zxdemo-id/", zxdemo.party_demozoo_ids_by_zxdemo_id, {}),
    path("adhoc/klubi/demoshow-prods/", klubi.demoshow, {}),
    path("adhoc/scenesat/monthly-releases/", scenesat.monthly, {}),
    path("adhoc/eq/demos/", eq.demos, {}),
    path("adhoc/group-abbreviations/", group_abbreviations.group_abbreviations, {}),
    path("adhoc/meteoriks/candidates/<int:year>/", meteoriks.candidates, {}),
    path("v1/", include(router.urls)),
]
