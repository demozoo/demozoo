from rest_framework import viewsets

from demoscene.models import Releaser
from productions.models import Production
from api.serializers import ProductionSerializer, ReleaserSerializer


class ProductionViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = Production.objects.all()
	serializer_class = ProductionSerializer


class ReleaserViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = Releaser.objects.all()
	serializer_class = ReleaserSerializer
