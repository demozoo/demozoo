from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

from zxdemo import views as zxdemo_views


admin.autodiscover()

urlpatterns = [
    url(r'^$', zxdemo_views.home, {}, 'zxdemo_home'),
    url(r'^index.php$', RedirectView.as_view(url='/')),

    url(r'^screens/(\d+)/$', zxdemo_views.show_screenshot, {}, 'zxdemo_show_screenshot'),

    url(r'^productions/$', zxdemo_views.productions, {}, 'zxdemo_productions'),
    url(r'^releases.php$', zxdemo_views.releases_redirect),
    url(r'^productions/(\d+)/$', zxdemo_views.production, {}, 'zxdemo_production'),
    url(r'^item.php$', zxdemo_views.production_redirect, {}),

    url(r'^scener_index_name.php$', RedirectView.as_view(url='/authors/')),
    url(r'^scener_index_activity.php$', RedirectView.as_view(url='/authors/')),
    url(r'^authors/$', zxdemo_views.authors, {}, 'zxdemo_authors'),
    url(r'^authors/(\d+)/$', zxdemo_views.author, {}, 'zxdemo_author'),
    url(r'^author.php$', zxdemo_views.author_redirect, {}),

    url(r'^partycalendar.php$', zxdemo_views.partycalendar_redirect),
    url(r'^parties/$', zxdemo_views.parties, {}, 'zxdemo_parties'),
    url(r'^parties/(\d+)/$', zxdemo_views.parties_year, {}, 'zxdemo_parties_year'),
    url(r'^party/(\d+)/$', zxdemo_views.party, {}, 'zxdemo_party'),
    url(r'^party.php$', zxdemo_views.party_redirect, {}),

    url(r'^rss.php$', zxdemo_views.rss, {}),
    url(r'^rss/$', zxdemo_views.rss, {}, 'zxdemo_rss'),

    url(r'^search/$', zxdemo_views.search, {}, 'zxdemo_search'),
    url(r'^search.php$', RedirectView.as_view(url='/search/', query_string=True)),

    url(r'^articles/$', zxdemo_views.articles, {}, 'zxdemo_articles'),
    url(r'^article_index.php$', RedirectView.as_view(url='/articles/')),

    url(r'^article/(\d+)/$', zxdemo_views.article, {}, 'zxdemo_article'),
    url(r'^article.php$', zxdemo_views.article_redirect, {}),

    url(r'^admin/', admin.site.urls),
]

handler404 = 'zxdemo.views.page_not_found'

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
