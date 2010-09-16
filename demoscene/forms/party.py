from django import forms
from demoscene.models import Party, PartySeries
from any_format_date_field import AnyFormatDateField

class PartyForm(forms.ModelForm):
	existing_party_series = forms.ModelChoiceField(label = 'Party series', queryset = PartySeries.objects.order_by('name'), required = False)
	new_party_series_name = forms.CharField(label = '- or, add a new one', required = False)
	name = forms.CharField(label = 'Party name')
	start_date = AnyFormatDateField()
	end_date = AnyFormatDateField()
	class Meta:
		model = Party
		fields = ('existing_party_series', 'new_party_series_name', 'start_date', 'end_date', 'name')

class EditPartyForm(forms.ModelForm):
	start_date = AnyFormatDateField()
	end_date = AnyFormatDateField()
	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date')

