from django.conf import settings
from django.contrib import admin
from django.urls import include, path


admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("demoscene.urls")),
    path("", include("homepage.urls")),
    path("", include("parties.urls")),
    path("", include("comments.urls")),
    path("", include("productions.urls")),
    path("", include("users.urls")),
    path("platforms/", include("platforms.urls")),
    path("search/", include("search.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("pages/", include("pages.urls")),
    path("sceneorg/", include("sceneorg.urls")),
    path("pouet/", include("pouet.urls")),
    path("janeway/", include("janeway.urls")),
    path("forums/", include("forums.urls")),
    path("api/", include("api.urls")),
    path("awards/", include("awards.urls")),
    path("bbs/", include("bbs.urls")),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
