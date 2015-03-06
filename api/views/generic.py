from rest_framework import viewsets

from demoscene.models import Releaser
from platforms.models import Platform
from productions.models import Production, ProductionType
from api.serializers import ProductionSerializer, ReleaserSerializer, PlatformSerializer, ProductionTypeSerializer


class ProductionViewSet(viewsets.ModelViewSet):
	queryset = Production.objects.all()
	serializer_class = ProductionSerializer


class PlatformViewSet(viewsets.ModelViewSet):
	queryset = Platform.objects.all()
	serializer_class = PlatformSerializer


class ProductionTypeViewSet(viewsets.ModelViewSet):
	queryset = ProductionType.objects.all()
	serializer_class = ProductionTypeSerializer


class ReleaserViewSet(viewsets.ModelViewSet):
	queryset = Releaser.objects.all()
	serializer_class = ReleaserSerializer
