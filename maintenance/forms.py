from __future__ import absolute_import, unicode_literals

from django import forms

from platforms.models import Platform
from productions.models import ProductionType


class ProductionFilterForm(forms.Form):
    platform = forms.ModelMultipleChoiceField(required=False, queryset=Platform.objects.all())
    production_type = forms.ModelMultipleChoiceField(required=False, queryset=ProductionType.objects.all())
