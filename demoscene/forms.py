from django import forms
from demoscene.models import Production, ProductionType

class ProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', )
		
class ProductionTypeForm(forms.Form):
	production_type = forms.ModelChoiceField(queryset = ProductionType.objects.all())

ProductionTypeFormSet = forms.formsets.formset_factory(ProductionTypeForm, can_delete = True)
