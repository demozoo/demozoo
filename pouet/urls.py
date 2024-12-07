from django.urls import re_path
from django.views.generic import RedirectView

from pouet import views


urlpatterns = [
    re_path(r"^$", RedirectView.as_view(url="/pouet/groups/")),
    re_path(r"^groups/$", views.groups, {}, "pouet_groups"),
    re_path(r"^groups/(\d+)/$", views.match_group, {}, "pouet_match_group"),
    re_path(r"^production-link/$", views.production_link, {}, "pouet_production_link"),
    re_path(r"^production-unlink/$", views.production_unlink, {}, "pouet_production_unlink"),
]
