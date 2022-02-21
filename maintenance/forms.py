from django import forms

from platforms.models import Platform
from productions.models import ProductionType


class ProductionFilterForm(forms.Form):
    platform = forms.ModelMultipleChoiceField(required=False, queryset=Platform.objects.all())
    production_type = forms.ModelMultipleChoiceField(required=False, queryset=ProductionType.objects.all())
    release_year = forms.IntegerField(required=False)
