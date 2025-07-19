from django import forms
from django.db.models import Count, Q
from django.utils.http import urlencode

from awards.models import PlatformGroup
from platforms.models import Platform
from productions.models import ProductionType


class ScreeningFilterForm(forms.Form):
    def __init__(self, event, *args, filter_options_by_event=True, **kwargs):
        """
        Initialize the form with the event's platforms.
        """
        super().__init__(*args, **kwargs)
        self.event = event

        if not event.has_unscreened_productions:
            # defult rating_count to "less than two ratings" if there are no unscreened productions
            self.fields["rating_count"].initial = "1"

        # Filter the platform group queryset to only those that belong to the event series of the event
        self.fields["platform_group"].queryset = PlatformGroup.objects.filter(event_series=event.series)

        if filter_options_by_event:
            # limit the queryset of the platform field to those represented
            # in event.screenable_productions()
            self.fields["platform"].queryset = Platform.objects.filter(
                id__in=event.screenable_productions().values_list("platforms__id", flat=True)
            ).distinct()

            # limit the queryset of the production_type field to those represented
            # in event.screenable_productions(), and their ancestors
            seen_prod_type_paths = (
                ProductionType.objects.filter(id__in=event.screenable_productions().values_list("types__id", flat=True))
                .distinct()
                .values_list("path", flat=True)
            )
            ancestor_paths = set()
            for path in seen_prod_type_paths:
                # take slices of the path to get all ancestors
                for i in range(ProductionType.steplen, len(path) + 1, ProductionType.steplen):
                    ancestor_paths.add(path[:i])

            self.fields["production_type"].queryset = ProductionType.objects.filter(path__in=ancestor_paths)

    platform_group = forms.ModelChoiceField(
        label="Platform group",
        empty_label="Any category",
        queryset=PlatformGroup.objects.all(),
        required=False,
    )
    platform = forms.ModelChoiceField(
        label="Platform",
        empty_label="Any platform",
        queryset=Platform.objects.all(),
        required=False,
    )
    production_type = forms.ModelChoiceField(
        label="Production type",
        empty_label="Any type",
        queryset=ProductionType.objects.all(),
        required=False,
    )
    has_youtube = forms.ChoiceField(
        label="Has YouTube video",
        choices=[("", "With or without"), ("yes", "With"), ("no", "Without")],
        required=False,
    )
    rating_count = forms.ChoiceField(
        label="Rating count",
        choices=[("", "Any number of ratings"), ("0", "Not been rated yet"), ("1", "Less than two ratings")],
        initial="0",
        required=False,
    )

    def filter(self, queryset):
        """
        Filter the queryset based on the form data.
        """
        if self.is_valid():
            if self.cleaned_data["platform"]:
                queryset = queryset.filter(platforms=self.cleaned_data["platform"])
            if self.cleaned_data["platform_group"]:
                platform_group = self.cleaned_data["platform_group"]
                platform_group_filter = Q(platforms__platform_groups=self.cleaned_data["platform_group"])
                if platform_group.include_no_platform:
                    platform_group_filter |= Q(platforms__isnull=True)
                queryset = queryset.filter(platform_group_filter)
            if self.cleaned_data["production_type"]:
                prod_types = ProductionType.get_tree(self.cleaned_data["production_type"])
                queryset = queryset.filter(types__in=prod_types)
            if self.cleaned_data["has_youtube"]:
                if self.cleaned_data["has_youtube"] == "yes":
                    queryset = queryset.filter(links__is_download_link=False, links__link_class="YoutubeVideo")
                elif self.cleaned_data["has_youtube"] == "no":
                    queryset = queryset.exclude(links__is_download_link=False, links__link_class="YoutubeVideo")
            if self.cleaned_data["rating_count"]:
                queryset = queryset.annotate(
                    rating_count=Count("screening_decisions", filter=Q(screening_decisions__event=self.event))
                ).filter(rating_count__lte=self.cleaned_data["rating_count"])
        return queryset

    def as_query_string(self):
        """
        Returns the form data as a querystring.
        """
        if not self.is_valid():
            return ""
        params = {}
        if self.cleaned_data["platform"]:
            params["platform"] = self.cleaned_data["platform"].pk
        if self.cleaned_data["platform_group"]:
            params["platform_group"] = self.cleaned_data["platform_group"].pk
        if self.cleaned_data["production_type"]:
            params["production_type"] = self.cleaned_data["production_type"].pk
        if self.cleaned_data["has_youtube"]:
            params["has_youtube"] = self.cleaned_data["has_youtube"]
        if self.cleaned_data["rating_count"]:
            params["rating_count"] = self.cleaned_data["rating_count"]
        return urlencode(params)
