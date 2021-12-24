from django_filters import rest_framework as filters
from django.db.models import Q

from bbs.models import BBS
from demoscene.models import Releaser
from parties.models import Party, PartySeries
from platforms.models import Platform
from productions.models import Production, ProductionType


class PlatformFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = Platform
        fields = []


class ProductionTypeFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = ProductionType
        fields = []


class ProductionFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='iexact')
    platform = filters.ModelMultipleChoiceFilter(field_name='platforms', queryset=Platform.objects.all())
    released_before = filters.DateFilter(
        field_name='release_date_date', lookup_expr='lt', label="Released before"
    )
    released_since = filters.DateFilter(
        field_name='release_date_date', lookup_expr='gte', label="Released since"
    )
    added_before = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='lt', label="Added before"
    )
    added_since = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte', label="Added since"
    )
    updated_before = filters.DateTimeFilter(
        field_name='updated_at', lookup_expr='lt', label="Updated before"
    )
    updated_since = filters.DateTimeFilter(
        field_name='updated_at', lookup_expr='gte', label="Updated since"
    )
    author = filters.NumberFilter(method='filter_author', label="Author ID")

    def filter_author(self, queryset, name, value):
        return queryset.filter(
            Q(author_nicks__releaser_id=value) | Q(author_affiliation_nicks__releaser_id=value)
        )

    class Meta:
        model = Production
        fields = ['supertype']


class ReleaserFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='iexact')
    country_code = filters.CharFilter(lookup_expr='iexact')
    added_before = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='lt', label="Added before"
    )
    added_since = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte', label="Added since"
    )
    updated_before = filters.DateTimeFilter(
        field_name='updated_at', lookup_expr='lt', label="Updated before"
    )
    updated_since = filters.DateTimeFilter(
        field_name='updated_at', lookup_expr='gte', label="Updated since"
    )

    class Meta:
        model = Releaser
        fields = ['is_group']


class PartySeriesFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = PartySeries
        fields = []


class PartyFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='iexact')
    start_date_before = filters.DateFilter(
        field_name='start_date_date', lookup_expr='lt', label="Start date before"
    )
    start_date_since = filters.DateFilter(
        field_name='start_date_date', lookup_expr='gte', label="Start date since"
    )
    country_code = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = Party
        fields = ['party_series']


class BBSFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='iexact')
    country_code = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = BBS
        fields = []
