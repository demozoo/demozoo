from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import PlatformHandler

platform_handler = Resource(PlatformHandler)

urlpatterns = patterns('',
	url(r'^platform/(?P<platform_id>\d+)/', platform_handler),
	url(r'^platforms/', platform_handler),
)
