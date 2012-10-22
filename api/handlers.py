from piston.handler import BaseHandler
from demoscene.models import Platform, ProductionType


class PlatformHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Platform
	fields = ('id', 'name')

	def read(self, request, platform_id=None):
		"""
			Returns a single platform if `platform_id` is given,
			otherwise the full set
		"""
		base = Platform.objects

		if platform_id:
			return base.get(pk=platform_id)
		else:
			return base.all()


class ProductionTypeHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = ProductionType
	fields = ('id', 'name')

	def read(self, request, prodtype_id=None):
		"""
			Returns a single production type if `prodtype_id` is given,
			otherwise the full set
		"""
		base = ProductionType.objects

		if prodtype_id:
			return base.get(pk=prodtype_id)
		else:
			return base.all()
