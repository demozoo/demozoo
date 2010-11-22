from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import ProductionHandler

production_handler = Resource(ProductionHandler)

urlpatterns = patterns('',
	url(r'^production/(\d+)/', production_handler),
	#url(r'^productions/', production_handler),
)
