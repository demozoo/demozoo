from django import forms
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from demoscene.models import Edit
from productions.models import ProductionType
from platforms.models import Platform
from parties.models import Party, PartySeries, Competition, PartyExternalLink
from demoscene.forms.common import ExternalLinkForm, BaseExternalLinkFormSet
from fuzzy_date_field import FuzzyDateField
from form_with_location import ModelFormWithLocation
from productions.fields.production_type_field import ProductionTypeChoiceField
from productions.fields.production_field import ProductionField


class PartyForm(ModelFormWithLocation):
	name = forms.CharField(label='Party name', help_text="e.g. Revision 2011")
	party_series_name = forms.CharField(label='Party series', help_text="e.g. Revision")
	start_date = FuzzyDateField(help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")')
	end_date = FuzzyDateField(help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")')
	scene_org_folder = forms.CharField(required=False, widget=forms.HiddenInput)

	def save(self, commit=True):
		try:
			self.instance.party_series = PartySeries.objects.get(name=self.cleaned_data['party_series_name'])
		except PartySeries.DoesNotExist:
			ps = PartySeries(name=self.cleaned_data['party_series_name'])
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
					link_class='PouetParty',
					parameter="%s/%s" % (self.instance.party_series.pouet_party_id, self.instance.start_date.date.year),
					party=self.instance
				)

			# create a Twitter link if we already know a Twitter username from the party series record
			if self.instance.party_series.twitter_username:
				PartyExternalLink.objects.create(
					link_class='TwitterAccount',
					parameter=self.instance.party_series.twitter_username,
					party=self.instance
				)

			# create a scene.org external link if folder path is passed in
			if self.cleaned_data['scene_org_folder']:
				PartyExternalLink.objects.create(
					party=self.instance,
					parameter=self.cleaned_data['scene_org_folder'],
					link_class='SceneOrgFolder')

		return self.instance

	def log_creation(self, user):
		Edit.objects.create(action_type='create_party', focus=self.instance,
			description=(u"Added party '%s'" % self.instance.name), user=user)

	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location', 'is_online', 'website', 'party_series_name')


class EditPartyForm(ModelFormWithLocation):
	start_date = FuzzyDateField(help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")')
	end_date = FuzzyDateField(help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")')

	@property
	def changed_data_description(self):
		descriptions = []
		changed_fields = self.changed_data
		if 'name' in changed_fields:
			descriptions.append(u"name to '%s'" % self.cleaned_data['name'])
		if 'start_date' in changed_fields:
			descriptions.append(u"start date to %s" % self.cleaned_data['start_date'])
		if 'end_date' in changed_fields:
			descriptions.append(u"end date to %s" % self.cleaned_data['end_date'])
		if 'tagline' in changed_fields:
			descriptions.append(u"tagline to '%s'" % self.cleaned_data['tagline'])
		if 'location' in changed_fields:
			descriptions.append(u"location to %s" % self.cleaned_data['location'])
		if 'website' in changed_fields:
			descriptions.append(u"website to %s" % self.cleaned_data['website'])
		if descriptions:
			return u"Set %s" % (u", ".join(descriptions))

	def log_edit(self, user):
		description = self.changed_data_description
		if description:
			Edit.objects.create(action_type='edit_party', focus=self.instance,
				description=description, user=user)

	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location', 'is_online', 'website')


class PartyEditNotesForm(forms.ModelForm):
	def log_edit(self, user):
		Edit.objects.create(action_type='edit_party_notes', focus=self.instance,
			description="Edited notes", user=user)

	class Meta:
		model = Party
		fields = ['notes']


class EditPartySeriesForm(forms.ModelForm):
	@property
	def changed_data_description(self):
		descriptions = []
		changed_fields = self.changed_data
		if 'name' in changed_fields:
			descriptions.append(u"name to '%s'" % self.cleaned_data['name'])
		if 'website' in changed_fields:
			descriptions.append(u"website to %s" % self.cleaned_data['website'])
		if 'twitter_username' in changed_fields:
			descriptions.append(u"Twitter username to %s" % self.cleaned_data['twitter_username'])
		if 'pouet_party_id' in changed_fields:
			descriptions.append(u"Pouet party ID to '%s'" % self.cleaned_data['pouet_party_id'])
		if descriptions:
			return u"Set %s" % (u", ".join(descriptions))

	def log_edit(self, user):
		description = self.changed_data_description
		if description:
			Edit.objects.create(action_type='edit_party', focus=self.instance,
				description=description, user=user)

	class Meta:
		model = PartySeries
		fields = ('name', 'website', 'twitter_username', 'pouet_party_id')
		widgets = {
			'twitter_username': forms.TextInput(attrs={'class': 'numeric'}),  # not really numeric, but box is the same size
			'pouet_party_id': forms.TextInput(attrs={'class': 'numeric'}),
		}


class PartySeriesEditNotesForm(forms.ModelForm):
	def log_edit(self, user):
		Edit.objects.create(action_type='edit_party_series_notes', focus=self.instance,
			description="Edited notes", user=user)

	class Meta:
		model = PartySeries
		fields = ['notes']


class CompetitionForm(forms.ModelForm):
	shown_date = FuzzyDateField(label="Date", required=False)
	production_type = ProductionTypeChoiceField(required=False, queryset=ProductionType.objects.all())
	platform = forms.ModelChoiceField(required=False, queryset=Platform.objects.all())

	def log_creation(self, user):
		Edit.objects.create(action_type='create_competiton', focus=self.instance, focus2=self.instance.party,
			description=(u"Added competition %s" % self.instance.name), user=user)

	@property
	def changed_data_description(self):
		descriptions = []
		changed_fields = self.changed_data
		if 'name' in changed_fields:
			descriptions.append(u"name to %s" % self.cleaned_data['name'])
		if 'shown_date' in changed_fields:
			descriptions.append(u"date to %s" % self.cleaned_data['shown_date'])
		if 'platform' in changed_fields:
			descriptions.append(u"platform to %s" % self.cleaned_data['platform'])
		if 'production_type' in changed_fields:
			descriptions.append(u"production type to %s" % self.cleaned_data['production_type'])
		if descriptions:
			return u"Set %s" % (u", ".join(descriptions))

	def log_edit(self, user):
		description = self.changed_data_description
		if description:
			Edit.objects.create(action_type='edit_competition', focus=self.instance,
				description=description, user=user)

	class Meta:
		model = Competition
		fields = ('name', 'shown_date', 'platform', 'production_type')


class PartyExternalLinkForm(ExternalLinkForm):
	class Meta:
		model = PartyExternalLink
		exclude = ['parameter', 'link_class', 'party']

PartyExternalLinkFormSet = inlineformset_factory(Party, PartyExternalLink,
	form=PartyExternalLinkForm, formset=BaseExternalLinkFormSet)


class PartyInvitationForm(forms.Form):
	production = ProductionField()

PartyInvitationFormset = formset_factory(PartyInvitationForm,
	can_delete=True, extra=1)


class PartyReleaseForm(forms.Form):
	production = ProductionField()

PartyReleaseFormset = formset_factory(PartyReleaseForm,
	can_delete=True, extra=1)
