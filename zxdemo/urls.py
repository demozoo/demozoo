from django.conf.urls import *
from django.views.generic.base import RedirectView

urlpatterns = patterns('zxdemo.views',
	(r'^$', 'home', {}, 'zxdemo_home'),
	(r'^index.php$', RedirectView.as_view(url='/')),
)
