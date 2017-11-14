from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from demoscene.models import Releaser
from parties.models import Party
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

	@detail_route()
	def productions(self, request, pk):
		releaser = Releaser.objects.get(pk=pk)
		queryset = releaser.productions().order_by('-release_date_date').prefetch_related(
			'platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser'
		)
		serializer = serializers.ProductionListingSerializer(
			queryset, many=True, context={'request': request}
		)
		return Response(serializer.data)

	@detail_route()
	def member_productions(self, request, pk):
		releaser = Releaser.objects.get(pk=pk)
		queryset = releaser.member_productions().order_by('-release_date_date').prefetch_related(
			'platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser'
		)
		serializer = serializers.ProductionListingSerializer(
			queryset, many=True, context={'request': request}
		)
		return Response(serializer.data)


class PartyViewSet(ListDetailModelViewSet):
	queryset = Party.objects.all()
	list_serializer_class = serializers.PartyListingSerializer
	serializer_class = serializers.PartySerializer
