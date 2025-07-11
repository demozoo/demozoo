from django import forms
from django.utils.http import urlencode

from platforms.models import Platform


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

    platform = forms.ModelChoiceField(
        label="Platform",
        queryset=Platform.objects.all(),
        required=False,
    )

    def filter(self, queryset):
        """
        Filter the queryset based on the form data.
        """
        if self.is_valid():
            if self.cleaned_data["platform"]:
                queryset = queryset.filter(platforms=self.cleaned_data["platform"])
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
        return urlencode(params)
