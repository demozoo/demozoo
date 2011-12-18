from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet, inlineformset_factory
from demoscene.models import Party, PartySeries, Competition, CompetitionPlacing, Platform, ProductionType, PartyExternalLink
from demoscene.forms.common import ExternalLinkForm
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
	scene_org_folder = forms.CharField(required=False, widget = forms.HiddenInput)
	
	def save(self, commit=True):
		try:
			self.instance.party_series = PartySeries.objects.get(name = self.cleaned_data['party_series_name'])
		except PartySeries.DoesNotExist:
			ps = PartySeries(name = self.cleaned_data['party_series_name'])
			ps.save()
			self.instance.party_series = ps
		
		self.instance.start_date = self.cleaned_data['start_date']
		self.instance.end_date = self.cleaned_data['end_date']
		
		# populate website field from party_series if not already specified
		if self.instance.party_series.website and not self.instance.website:
			self.instance.website = self.instance.party_series.website
		# conversely, fill in the website field on party_series if it's given here and we don't have one already
		elif self.instance.website and not self.instance.party_series.website:
			self.instance.party_series.website = self.instance.website
			self.instance.party_series.save()
		
		super(PartyForm, self).save(commit=commit)
		
		if commit:
			# create a Pouet link if we already know the Pouet party id from the party series record
			if self.instance.start_date and self.instance.party_series.pouet_party_id:
				PartyExternalLink.objects.create(
					link_class = 'PouetParty',
					parameter = "%s/%s" % (self.instance.party_series.pouet_party_id, self.instance.start_date.date.year),
					party = self.instance
				)
			
			# create a Twitter link if we already know a Twitter username from the party series record
			if self.instance.party_series.twitter_username:
				PartyExternalLink.objects.create(
					link_class = 'TwitterAccount',
					parameter = self.instance.party_series.twitter_username,
					party = self.instance
				)
			
			# create a scene.org external link if folder path is passed in
			if self.cleaned_data['scene_org_folder']:
				PartyExternalLink.objects.create(
					party = self.instance,
					parameter = self.cleaned_data['scene_org_folder'],
					link_class = 'SceneOrgFolder')
		
		return self.instance
	
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

class PartyExternalLinkForm(ExternalLinkForm):
	class Meta:
		model = PartyExternalLink
		fields = ['url']
PartyExternalLinkFormSet = inlineformset_factory(Party, PartyExternalLink, form=PartyExternalLinkForm)
