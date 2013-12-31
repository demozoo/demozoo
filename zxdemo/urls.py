from django.conf.urls import *

urlpatterns = patterns('zxdemo.views',
	(r'^$', 'home', {}, 'zxdemo_home'),
)
