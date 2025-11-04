from django import forms
from django.db.models import Count, Q
from django.http import QueryDict

from awards.models import PlatformGroup, ScreeningComment
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
            self.fields["platforms"].queryset = Platform.objects.filter(
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

            self.fields["production_types"].queryset = ProductionType.objects.filter(path__in=ancestor_paths)

    platform_group = forms.ModelChoiceField(
        label="Platform group",
        empty_label="Any category",
        queryset=PlatformGroup.objects.all(),
        required=False,
    )
    platforms = forms.ModelMultipleChoiceField(
        label="Platforms",
        queryset=Platform.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    production_types = forms.ModelMultipleChoiceField(
        label="Production types",
        queryset=ProductionType.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
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
            if self.cleaned_data["platforms"]:
                queryset = queryset.filter(platforms__in=self.cleaned_data["platforms"]).distinct()
            if self.cleaned_data["platform_group"]:
                platform_group = self.cleaned_data["platform_group"]
                platform_group_filter = Q(platforms__platform_groups=self.cleaned_data["platform_group"])
                if platform_group.include_no_platform:
                    platform_group_filter |= Q(platforms__isnull=True)
                queryset = queryset.filter(platform_group_filter)
            if self.cleaned_data["production_types"]:
                prod_type_trees = [
                    ProductionType.get_tree(prod_type) for prod_type in self.cleaned_data["production_types"]
                ]
                prod_types_q = Q(types__in=prod_type_trees[0])
                for tree in prod_type_trees[1:]:
                    prod_types_q |= Q(types__in=tree)
                queryset = queryset.filter(prod_types_q).distinct()
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
        params = QueryDict(mutable=True)
        if self.cleaned_data["platforms"]:
            params.setlist("platforms", [platform.pk for platform in self.cleaned_data["platforms"]])
        if self.cleaned_data["platform_group"]:
            params["platform_group"] = self.cleaned_data["platform_group"].pk
        if self.cleaned_data["production_types"]:
            params.setlist("production_types", [prod_type.pk for prod_type in self.cleaned_data["production_types"]])
        if self.cleaned_data["has_youtube"]:
            params["has_youtube"] = self.cleaned_data["has_youtube"]
        if self.cleaned_data["rating_count"]:
            params["rating_count"] = self.cleaned_data["rating_count"]
        return params.urlencode()


class ScreeningCommentForm(forms.ModelForm):
    """
    Form for submitting comments on productions during screening.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comment"].label = "Add a comment"

    class Meta:
        model = ScreeningComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
        }
