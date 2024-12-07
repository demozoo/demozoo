from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
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
    Extension to ReadOnlyModelViewSet to allow us to have different field lists for
    list and detail views. Requires the serializer to inherit OutputFieldsMixin
    """
    listing_fields = None

    @cached_property
    def output_fields(self):
        fields_param = self.request.GET.get('fields')
        if fields_param:
            return fields_param.split(',')
        elif self.action == 'list' and self.listing_fields is not None:
            return self.listing_fields
        else:
            return []

    def get_serializer(self, *args, **kwargs):
        if self.output_fields:
            kwargs['fields'] = self.output_fields
        return super().get_serializer(*args, **kwargs)


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


class ProductionViewSet(ListDetailModelViewSet):
    queryset = Production.objects.prefetch_related(
        'platforms', 'types', 'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'tags'
    )
    serializer_class = serializers.ProductionSerializer
    filterset_class = filters.ProductionFilter
    ordering_fields = ['id', 'sortable_title', 'release_date_date', 'supertype']
    listing_fields = serializers.PRODUCTION_LISTING_FIELDS


class ReleaserViewSet(ListDetailModelViewSet):
    queryset = Releaser.objects.all()
    serializer_class = serializers.ReleaserSerializer
    filterset_class = filters.ReleaserFilter
    lookup_value_regex = r'\d+'
    ordering_fields = ['id', 'name']
    listing_fields = ['url', 'id', 'name', 'is_group']

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


class PartySeriesViewSet(ListDetailModelViewSet):
    queryset = PartySeries.objects.all()
    serializer_class = serializers.PartySeriesSerializer
    filterset_class = filters.PartySeriesFilter
    ordering_fields = ['id', 'name']
    listing_fields = serializers.PARTY_SERIES_LISTING_FIELDS


class PartyViewSet(ListDetailModelViewSet):
    queryset = Party.objects.all()
    serializer_class = serializers.PartySerializer
    filterset_class = filters.PartyFilter
    ordering_fields = ['id', 'name', 'start_date_date', 'end_date_date', 'country_code']
    listing_fields = serializers.PARTY_LISTING_FIELDS


class BBSViewSet(ListDetailModelViewSet):
    queryset = BBS.objects.prefetch_related(
        'tags', 'bbstros__platforms', 'bbstros__types', 'bbstros__author_nicks__releaser',
        'bbstros__author_affiliation_nicks__releaser', 'bbstros__tags'
    )
    serializer_class = serializers.BBSSerializer
    filterset_class = filters.BBSFilter
    ordering_fields = ['id', 'name']
    listing_fields = [
        'url', 'demozoo_url', 'id', 'name', 'location',
        'latitude', 'longitude', 'tags',
    ]
