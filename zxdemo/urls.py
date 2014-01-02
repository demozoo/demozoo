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

	(r'^admin/', include(admin.site.urls)),
)
