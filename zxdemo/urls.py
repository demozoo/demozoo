from django.conf.urls import *
from django.views.generic.base import RedirectView
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('zxdemo.views',
	(r'^$', 'home', {}, 'zxdemo_home'),
	(r'^index.php$', RedirectView.as_view(url='/')),

	(r'^screens/(\d+)/$', 'show_screenshot', {}, 'zxdemo_show_screenshot'),

	(r'^productions/$', 'productions', {}, 'zxdemo_productions'),
	(r'^releases.php$', 'releases_redirect'),
	(r'^productions/(\d+)/$', 'production', {}, 'zxdemo_production'),
	(r'^item.php$', 'production_redirect', {}),

	(r'^scener_index_name.php$', RedirectView.as_view(url='/authors/')),
	(r'^scener_index_activity.php$', RedirectView.as_view(url='/authors/')),
	(r'^authors/$', 'authors', {}, 'zxdemo_authors'),
	(r'^authors/(\d+)/$', 'author', {}, 'zxdemo_author'),
	(r'^author.php$', 'author_redirect', {}),

	(r'^partycalendar.php$', 'partycalendar_redirect'),
	(r'^parties/$', 'parties', {}, 'zxdemo_parties'),
	(r'^parties/(\d+)/$', 'parties_year', {}, 'zxdemo_parties_year'),
	(r'^party/(\d+)/$', 'party', {}, 'zxdemo_party'),
	(r'^party.php$', 'party_redirect', {}),

	(r'^rss.php$', 'rss', {}),
	(r'^rss/$', 'rss', {}, 'zxdemo_rss'),

	(r'^search/$', 'search', {}, 'zxdemo_search'),
	(r'^search.php$', RedirectView.as_view(url='/search/', query_string=True)),

	(r'^articles/$', 'articles', {}, 'zxdemo_articles'),
	(r'^article_index.php$', RedirectView.as_view(url='/articles/')),

	(r'^article/(\d+)/$', 'article', {}, 'zxdemo_article'),
	(r'^article.php$', 'article_redirect', {}),

	(r'^admin/', include(admin.site.urls)),
)

handler404 = 'zxdemo.views.page_not_found'
