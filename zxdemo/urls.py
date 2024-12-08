from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from zxdemo import views as zxdemo_views


admin.autodiscover()

urlpatterns = [
    path("", zxdemo_views.home, {}, "zxdemo_home"),
    path("index.php", RedirectView.as_view(url="/")),
    path("screens/<int:screenshot_id>/", zxdemo_views.show_screenshot, {}, "zxdemo_show_screenshot"),
    path("productions/", zxdemo_views.productions, {}, "zxdemo_productions"),
    path("releases.php", zxdemo_views.releases_redirect),
    path("productions/<int:production_id>/", zxdemo_views.production, {}, "zxdemo_production"),
    path("item.php", zxdemo_views.production_redirect, {}),
    path("scener_index_name.php", RedirectView.as_view(url="/authors/")),
    path("scener_index_activity.php", RedirectView.as_view(url="/authors/")),
    path("authors/", zxdemo_views.authors, {}, "zxdemo_authors"),
    path("authors/<int:releaser_id>/", zxdemo_views.author, {}, "zxdemo_author"),
    path("author.php", zxdemo_views.author_redirect, {}),
    path("partycalendar.php", zxdemo_views.partycalendar_redirect),
    path("parties/", zxdemo_views.parties, {}, "zxdemo_parties"),
    path("parties/<int:year>/", zxdemo_views.parties_year, {}, "zxdemo_parties_year"),
    path("party/<int:party_id>/", zxdemo_views.party, {}, "zxdemo_party"),
    path("party.php", zxdemo_views.party_redirect, {}),
    path("rss.php", zxdemo_views.rss, {}),
    path("rss/", zxdemo_views.rss, {}, "zxdemo_rss"),
    path("search/", zxdemo_views.search, {}, "zxdemo_search"),
    path("search.php", RedirectView.as_view(url="/search/", query_string=True)),
    path("articles/", zxdemo_views.articles, {}, "zxdemo_articles"),
    path("article_index.php", RedirectView.as_view(url="/articles/")),
    path("article/<int:zxdemo_id>/", zxdemo_views.article, {}, "zxdemo_article"),
    path("article.php", zxdemo_views.article_redirect, {}),
    path("admin/", admin.site.urls),
]

handler404 = "zxdemo.views.page_not_found"

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
