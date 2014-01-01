from django.conf.urls import *
from django.views.generic.base import RedirectView
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('zxdemo.views',
	(r'^$', 'home', {}, 'zxdemo_home'),
	(r'^index.php$', RedirectView.as_view(url='/')),

	(r'^admin/', include(admin.site.urls)),
)
