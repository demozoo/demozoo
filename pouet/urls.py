from django.urls import path
from django.views.generic import RedirectView

from pouet import views


urlpatterns = [
    path("", RedirectView.as_view(url="/pouet/groups/")),
    path("groups/", views.groups, {}, "pouet_groups"),
    path("groups/<int:releaser_id>/", views.match_group, {}, "pouet_match_group"),
    path("production-link/", views.production_link, {}, "pouet_production_link"),
    path("production-unlink/", views.production_unlink, {}, "pouet_production_unlink"),
    path("nogroup-prods/", views.nogroup_prods, {}, "pouet_nogroup_prods"),
]
