from django import forms
from django.utils.http import urlencode

from platforms.models import Platform
from productions.models import ProductionType


class ScreeningFilterForm(forms.Form):
    def __init__(self, event, *args, **kwargs):
        """
        Initialize the form with the event's platforms.
        """
        super().__init__(*args, **kwargs)

        if event:
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

    platform = forms.ModelChoiceField(
        label="Platform",
        queryset=Platform.objects.all(),
        required=False,
    )
    production_type = forms.ModelChoiceField(
        label="Production type",
        queryset=ProductionType.objects.all(),
        required=False,
    )
    has_youtube = forms.ChoiceField(
        label="Has YouTube video",
        choices=[("", "Any"), ("yes", "Yes"), ("no", "No")],
        required=False,
    )

    def filter(self, queryset):
        """
        Filter the queryset based on the form data.
        """
        if self.is_valid():
            if self.cleaned_data["platform"]:
                queryset = queryset.filter(platforms=self.cleaned_data["platform"])
            if self.cleaned_data["production_type"]:
                prod_types = ProductionType.get_tree(self.cleaned_data["production_type"])
                queryset = queryset.filter(types__in=prod_types)
            if self.cleaned_data["has_youtube"]:
                if self.cleaned_data["has_youtube"] == "yes":
                    queryset = queryset.filter(links__is_download_link=False, links__link_class="YoutubeVideo")
                elif self.cleaned_data["has_youtube"] == "no":
                    queryset = queryset.exclude(links__is_download_link=False, links__link_class="YoutubeVideo")
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
        if self.cleaned_data["production_type"]:
            params["production_type"] = self.cleaned_data["production_type"].pk
        if self.cleaned_data["has_youtube"]:
            params["has_youtube"] = self.cleaned_data["has_youtube"]
        return urlencode(params)
