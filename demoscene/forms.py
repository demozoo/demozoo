from django import forms
from demoscene.models import Production

class ProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', )