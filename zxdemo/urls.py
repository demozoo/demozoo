from django.conf import settings
from django.urls import include, re_path
from django.contrib import admin
from django.views.generic.base import RedirectView

from zxdemo import views as zxdemo_views


admin.autodiscover()

urlpatterns = [
    re_path(r'^$', zxdemo_views.home, {}, 'zxdemo_home'),
    re_path(r'^index.php$', RedirectView.as_view(url='/')),

    re_path(r'^screens/(\d+)/$', zxdemo_views.show_screenshot, {}, 'zxdemo_show_screenshot'),

    re_path(r'^productions/$', zxdemo_views.productions, {}, 'zxdemo_productions'),
    re_path(r'^releases.php$', zxdemo_views.releases_redirect),
    re_path(r'^productions/(\d+)/$', zxdemo_views.production, {}, 'zxdemo_production'),
    re_path(r'^item.php$', zxdemo_views.production_redirect, {}),

    re_path(r'^scener_index_name.php$', RedirectView.as_view(url='/authors/')),
    re_path(r'^scener_index_activity.php$', RedirectView.as_view(url='/authors/')),
    re_path(r'^authors/$', zxdemo_views.authors, {}, 'zxdemo_authors'),
    re_path(r'^authors/(\d+)/$', zxdemo_views.author, {}, 'zxdemo_author'),
    re_path(r'^author.php$', zxdemo_views.author_redirect, {}),

    re_path(r'^partycalendar.php$', zxdemo_views.partycalendar_redirect),
    re_path(r'^parties/$', zxdemo_views.parties, {}, 'zxdemo_parties'),
    re_path(r'^parties/(\d+)/$', zxdemo_views.parties_year, {}, 'zxdemo_parties_year'),
    re_path(r'^party/(\d+)/$', zxdemo_views.party, {}, 'zxdemo_party'),
    re_path(r'^party.php$', zxdemo_views.party_redirect, {}),

    re_path(r'^rss.php$', zxdemo_views.rss, {}),
    re_path(r'^rss/$', zxdemo_views.rss, {}, 'zxdemo_rss'),

    re_path(r'^search/$', zxdemo_views.search, {}, 'zxdemo_search'),
    re_path(r'^search.php$', RedirectView.as_view(url='/search/', query_string=True)),

    re_path(r'^articles/$', zxdemo_views.articles, {}, 'zxdemo_articles'),
    re_path(r'^article_index.php$', RedirectView.as_view(url='/articles/')),

    re_path(r'^article/(\d+)/$', zxdemo_views.article, {}, 'zxdemo_article'),
    re_path(r'^article.php$', zxdemo_views.article_redirect, {}),

    re_path(r'^admin/', admin.site.urls),
]

handler404 = 'zxdemo.views.page_not_found'

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar
    urlpatterns = [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
