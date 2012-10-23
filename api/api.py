from tastypie.resources import ModelResource
from demoscene.models import Platform, ProductionType


class PlatformResource(ModelResource):
	class Meta:
		queryset = Platform.objects.all()
		resource_name = 'platform'
		fields = ['id', 'name']
		limit = 0  # can safely show all platforms at once


class ProductionTypeResource(ModelResource):
	class Meta:
		queryset = ProductionType.objects.all()
		resource_name = 'production_type'
		fields = ['id', 'name']
		limit = 0  # can safely show all platforms at once
