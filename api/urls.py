from django.conf.urls.defaults import *
from tastypie.api import Api
from api import PlatformResource, ProductionTypeResource

v1_api = Api(api_name='v1')
v1_api.register(PlatformResource())
v1_api.register(ProductionTypeResource())

urlpatterns = patterns('',
	(r'^', include(v1_api.urls)),
)
