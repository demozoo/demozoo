from django.conf.urls import *
from django.views.generic.base import RedirectView
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('zxdemo.views',
	(r'^$', 'home', {}, 'zxdemo_home'),
	(r'^index.php$', RedirectView.as_view(url='/')),

	(r'^screens/(\d+)/', 'show_screenshot', {}, 'zxdemo_show_screenshot'),

	(r'^productions/(\d+)/', 'production', {}, 'zxdemo_production'),
	(r'^item.php', 'production_redirect', {}),

	(r'^scener_index_name.php$', RedirectView.as_view(url='/authors')),
	(r'^scener_index_activity.php$', RedirectView.as_view(url='/authors')),
	(r'^authors/$', 'authors', {}, 'zxdemo_authors'),
	(r'^authors/(\d+)/', 'author', {}, 'zxdemo_author'),
	(r'^author.php', 'author_redirect', {}),

	(r'^admin/', include(admin.site.urls)),
)
