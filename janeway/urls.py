from django.urls import re_path
from django.views.generic import RedirectView

from janeway import views


urlpatterns = [
    re_path(r"^$", RedirectView.as_view(url="/janeway/authors/")),
    re_path(r"^authors/$", views.authors, {}, "janeway_authors"),
    re_path(r"^authors/(\d+)/$", views.match_author, {}, "janeway_match_author"),
    re_path(r"^production-link/$", views.production_link, {}, "janeway_production_link"),
    re_path(r"^production-unlink/$", views.production_unlink, {}, "janeway_production_unlink"),
    re_path(r"^production-import/$", views.production_import, {}, "janeway_production_import"),
    re_path(
        r"^import-all-author-productions/$",
        views.import_all_author_productions,
        {},
        "janeway_import_all_author_productions",
    ),
]
