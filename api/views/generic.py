from rest_framework import viewsets

from demoscene.models import Releaser
from platforms.models import Platform
from productions.models import Production, ProductionType
from api import serializers


class ListDetailModelViewSet(viewsets.ReadOnlyModelViewSet):
	"""
	extension to ReadOnlyModelViewSet to allow us to have different serializer classes for
	list and detail views. (seriously, we can't do this out of the box?)
	"""
	def get_serializer_class(self):
		if self.action == 'list':
			return self.list_serializer_class
		else:
			return self.serializer_class


class PlatformViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Platform.objects.all()
	serializer_class = serializers.PlatformSerializer

class ProductionTypeViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ProductionType.objects.all()
	serializer_class = serializers.ProductionTypeSerializer


class ProductionViewSet(ListDetailModelViewSet):
	queryset = Production.objects.prefetch_related('platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser')
	list_serializer_class = serializers.ProductionListingSerializer
	serializer_class = serializers.ProductionSerializer


class ReleaserViewSet(ListDetailModelViewSet):
	queryset = Releaser.objects.all()
	list_serializer_class = serializers.ReleaserListingSerializer
	serializer_class = serializers.ReleaserSerializer
