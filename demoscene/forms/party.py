from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet, inlineformset_factory
from demoscene.models import Party, PartySeries, Competition, CompetitionPlacing, Platform, ProductionType, PartyExternalLink
from fuzzy_date_field import FuzzyDateField
from production_field import ProductionField
from byline_field import BylineField
from form_with_location import ModelFormWithLocation
from production_type_field import ProductionTypeChoiceField

class PartyForm(ModelFormWithLocation):
	name = forms.CharField(label = 'Party name', help_text = "e.g. Revision 2011")
	party_series_name = forms.CharField(label = 'Party series', help_text = "e.g. Revision")
	start_date = FuzzyDateField(help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
	end_date = FuzzyDateField(help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location', 'website', 'party_series_name')

class EditPartyForm(ModelFormWithLocation):
	start_date = FuzzyDateField(help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
	end_date = FuzzyDateField(help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location', 'website')

class PartyEditNotesForm(forms.ModelForm):
	class Meta:
		model = Party
		fields = ['notes']

class EditPartySeriesForm(forms.ModelForm):
	class Meta:
		model = PartySeries
		fields = ('name', 'website', 'twitter_username', 'pouet_party_id')
		widgets = {
			'twitter_username': forms.TextInput(attrs={'class': 'numeric'}), # not really numeric, but box is the same size
			'pouet_party_id': forms.TextInput(attrs={'class': 'numeric'}),
		}

class PartySeriesEditNotesForm(forms.ModelForm):
	class Meta:
		model = PartySeries
		fields = ['notes']

class CompetitionForm(forms.ModelForm):
	shown_date = FuzzyDateField(label = "Date", required = False)
	production_type = ProductionTypeChoiceField(required = False, queryset = ProductionType.objects.all())
	platform = forms.ModelChoiceField(required = False, queryset = Platform.objects.all())
	class Meta:
		model = Competition
		fields = ('name', 'shown_date', 'platform', 'production_type')

class PartyExternalLinkForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(PartyExternalLinkForm, self).__init__(*args, **kwargs)
		self.fields['url'] = forms.CharField(label='URL', initial=self.instance.url)
	
	def save(self, commit = True):
		instance = super(PartyExternalLinkForm, self).save(commit = False)
		instance.url = self.cleaned_data['url']
		if commit:
			instance.save()
		return instance
	
	class Meta:
		model = PartyExternalLink
		fields = ['url']
PartyExternalLinkFormSet = inlineformset_factory(Party, PartyExternalLink, form=PartyExternalLinkForm)
