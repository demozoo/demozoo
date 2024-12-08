from django.urls import path
from django.views.generic import RedirectView

from janeway import views


urlpatterns = [
    path("", RedirectView.as_view(url="/janeway/authors/")),
    path("authors/", views.authors, {}, "janeway_authors"),
    path("authors/<int:releaser_id>/", views.match_author, {}, "janeway_match_author"),
    path("production-link/", views.production_link, {}, "janeway_production_link"),
    path("production-unlink/", views.production_unlink, {}, "janeway_production_unlink"),
    path("production-import/", views.production_import, {}, "janeway_production_import"),
    path(
        "import-all-author-productions/",
        views.import_all_author_productions,
        {},
        "janeway_import_all_author_productions",
    ),
]
