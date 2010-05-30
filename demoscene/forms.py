from django import forms
from demoscene.models import Production, ProductionType, Platform

class ProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', )
		
class ProductionTypeForm(forms.Form):
	production_type = forms.ModelChoiceField(queryset = ProductionType.objects.order_by('name'))

ProductionTypeFormSet = forms.formsets.formset_factory(ProductionTypeForm, can_delete = True)

class ProductionPlatformForm(forms.Form):
	platform = forms.ModelChoiceField(queryset = Platform.objects.order_by('name'))

ProductionPlatformFormSet = forms.formsets.formset_factory(ProductionPlatformForm, can_delete = True)
