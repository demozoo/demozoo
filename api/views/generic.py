from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import filters, serializers
from bbs.models import BBS
from demoscene.models import Releaser
from parties.models import Party, PartySeries
from platforms.models import Platform
from productions.models import Production, ProductionType


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
    filterset_class = filters.PlatformFilter
    ordering_fields = ['id', 'name']


class ProductionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductionType.objects.all()
    serializer_class = serializers.ProductionTypeSerializer
    filterset_class = filters.ProductionTypeFilter
    ordering_fields = ['id', 'name', 'path']


class ProductionViewSet(viewsets.ReadOnlyModelViewSet):
    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs['fields'] = serializers.PRODUCTION_LISTING_FIELDS
        return super().get_serializer(*args, **kwargs)

    queryset = Production.objects.prefetch_related(
        'platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'tags'
    )
    serializer_class = serializers.ProductionSerializer
    filterset_class = filters.ProductionFilter
    ordering_fields = ['id', 'sortable_title', 'release_date_date', 'supertype']


class ReleaserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Releaser.objects.all()
    serializer_class = serializers.ReleaserSerializer
    filterset_class = filters.ReleaserFilter
    lookup_value_regex = r'\d+'
    ordering_fields = ['id', 'name']

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs['fields'] = ['url', 'id', 'name', 'is_group']
        return super().get_serializer(*args, **kwargs)

    @action(detail=True)
    def productions(self, request, pk):
        releaser = get_object_or_404(Releaser, pk=pk)
        queryset = releaser.productions().order_by('-release_date_date').prefetch_related(
            'platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'tags'
        )
        serializer = serializers.ProductionSerializer(
            queryset, many=True, context={'request': request},
            fields=serializers.PRODUCTION_LISTING_FIELDS,
        )
        return Response(serializer.data)

    @action(detail=True)
    def member_productions(self, request, pk):
        releaser = get_object_or_404(Releaser, pk=pk)
        queryset = releaser.member_productions().order_by('-release_date_date').prefetch_related(
            'platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'tags'
        )
        serializer = serializers.ProductionSerializer(
            queryset, many=True, context={'request': request},
            fields=serializers.PRODUCTION_LISTING_FIELDS
        )
        return Response(serializer.data)


class PartySeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PartySeries.objects.all()
    serializer_class = serializers.PartySeriesSerializer
    filterset_class = filters.PartySeriesFilter
    ordering_fields = ['id', 'name']

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs['fields'] = serializers.PARTY_SERIES_LISTING_FIELDS
        return super().get_serializer(*args, **kwargs)


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Party.objects.all()
    serializer_class = serializers.PartySerializer
    filterset_class = filters.PartyFilter
    ordering_fields = ['id', 'name', 'start_date_date', 'end_date_date', 'country_code']

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs['fields'] = serializers.PARTY_LISTING_FIELDS
        return super().get_serializer(*args, **kwargs)


class BBSViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BBS.objects.prefetch_related('tags')
    serializer_class = serializers.BBSSerializer
    filterset_class = filters.BBSFilter
    ordering_fields = ['id', 'name']

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs['fields'] = [
                'url', 'demozoo_url', 'id', 'name', 'location',
                'latitude', 'longitude', 'tags',
            ]
        return super().get_serializer(*args, **kwargs)
