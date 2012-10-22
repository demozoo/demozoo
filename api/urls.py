from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import PlatformHandler, ProductionTypeHandler

platform_handler = Resource(PlatformHandler)
production_type_handler = Resource(ProductionTypeHandler)

urlpatterns = patterns('',
	url(r'^platform/(?P<platform_id>\d+)/', platform_handler),
	url(r'^platforms/', platform_handler),
	url(r'^production_type/(?P<prodtype_id>\d+)/', production_type_handler),
	url(r'^production_types/', production_type_handler),
)
