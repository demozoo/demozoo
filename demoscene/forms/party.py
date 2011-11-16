from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet
from demoscene.models import Party, PartySeries, Competition, CompetitionPlacing, Platform, ProductionType
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
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location', 'party_series_name')

class EditPartyForm(ModelFormWithLocation):
	start_date = FuzzyDateField(help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
	end_date = FuzzyDateField(help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location')

class PartyEditNotesForm(forms.ModelForm):
	class Meta:
		model = Party
		fields = ['notes']

class PartyEditExternalLinksForm(forms.ModelForm):
	class Meta:
		model = Party
		fields = Party.external_site_ref_field_names + ['pouet_party_when']
		widgets = {
			'twitter_username': forms.TextInput(attrs={'class': 'numeric'}), # not really numeric, but box is the same size
			'demoparty_net_url_fragment': forms.TextInput(attrs={'class': 'numeric'}), # not really numeric, but box is the same size
			'slengpung_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'pouet_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'pouet_party_when': forms.TextInput(attrs={'class': 'numeric'}),
			'bitworld_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'csdb_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'breaks_amiga_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'zxdemo_party_id': forms.TextInput(attrs={'class': 'numeric'}),
		}

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
