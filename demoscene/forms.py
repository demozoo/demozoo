from django import forms
from demoscene.models import Production, ProductionType, Platform, Releaser, DownloadLink, Nick, Party, PartySeries
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, modelformset_factory

from geocode import geocode
from django.core.exceptions import ValidationError

import timelib # for any-format date parsing
import datetime
from django.core import validators

class AnyFormatDateField(forms.DateField):
	widget = forms.DateInput(format = '%e %b %Y', attrs={'class':'date'})
	def to_python(self, value):
		"""
		Validates that the input can be converted to a date. Returns a Python
		datetime.date object.
		"""
		if value in validators.EMPTY_VALUES:
			return None
		if isinstance(value, datetime.datetime):
			return value.date()
		if isinstance(value, datetime.date):
			return value
		try:
			return timelib.strtodatetime(value).date()
		except ValueError:
			raise ValidationError(self.error_messages['invalid'])
		

class ProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', )

class AdminProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', 'notes')

class ProductionTypeForm(forms.Form):
	production_type = forms.ModelChoiceField(queryset = ProductionType.objects.order_by('name'))

ProductionTypeFormSet = formset_factory(ProductionTypeForm, can_delete = True)

class ProductionPlatformForm(forms.Form):
	platform = forms.ModelChoiceField(queryset = Platform.objects.order_by('name'))

ProductionPlatformFormSet = formset_factory(ProductionPlatformForm, can_delete = True)

DownloadLinkFormSet = inlineformset_factory(Production, DownloadLink, extra=1)


class CreateGroupForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name',)

class CreateScenerForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name',)

class ScenerEditLocationForm(forms.ModelForm):
	def clean_location(self):
		if self.cleaned_data['location']:
			if self.instance and self.instance.location == self.cleaned_data['location']:
				self.location_has_changed = False
			else:
				self.location_has_changed = True
				# look up new location
				self.geocoded_location = geocode(self.cleaned_data['location'])
				if not self.geocoded_location:
					raise ValidationError('Location not recognised')
					
		return self.cleaned_data['location']
	
	def save(self, commit = True, **kwargs):
		model = super(forms.ModelForm, self).save(commit = False, **kwargs)
		
		if self.cleaned_data['location']:
			if self.location_has_changed:
				model.location = self.geocoded_location['location']
				model.country_code = self.geocoded_location['country_code']
				model.latitude = self.geocoded_location['latitude']
				model.longitude = self.geocoded_location['longitude']
				model.woe_id = self.geocoded_location['woeid']
		else:
			# clear location data
			model.country_code = ''
			model.latitude = None
			model.longitude = None
			model.woe_id = None
		
		if commit:
			model.save()
			
		return model
	
	class Meta:
		model = Releaser
		fields = ('location',)

class ScenerEditExternalLinksForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = Releaser.external_site_ref_field_names
		widgets = {
			'sceneid_user_id': forms.TextInput(attrs={'class': 'numeric'}),
			'slengpung_user_id': forms.TextInput(attrs={'class': 'numeric'}),
			'amp_author_id': forms.TextInput(attrs={'class': 'numeric'}),
			'csdb_author_id': forms.TextInput(attrs={'class': 'numeric'}),
			'nectarine_author_id': forms.TextInput(attrs={'class': 'numeric'}),
			'bitjam_author_id': forms.TextInput(attrs={'class': 'numeric'}),
			'artcity_author_id': forms.TextInput(attrs={'class': 'numeric'}),
			'mobygames_author_id': forms.TextInput(attrs={'class': 'numeric'}),
		}

class ReleaserEditNotesForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ['notes']

class NickForm(forms.ModelForm):
	nick_variant_list = forms.CharField(label = "Other spellings / abbreviations of this name", required = False,
		help_text = "(as a comma-separated list)")
	
	def __init__(self, releaser, *args, **kwargs):
		super(NickForm, self).__init__(*args, **kwargs)
		if kwargs.has_key('instance'):
			instance = kwargs['instance']
			self.initial['nick_variant_list'] = instance.nick_variant_list
		else:
			instance = None
		
		# allow them to set this as the primary nick, unless they're editing the primary nick now
		if not (instance and instance.name == releaser.name):
			self.fields['override_primary_nick'] = forms.BooleanField(
				label = "Use this as their preferred nick, instead of '%s'" % releaser.name,
				required = False)
	
	def save(self, commit = True):
		instance = super(NickForm, self).save(commit=False)
		instance.nick_variant_list = self.cleaned_data['nick_variant_list']
		if commit:
			instance.save()
		return instance
	
	class Meta:
		model = Nick

class ScenerNickForm(NickForm):
	class Meta(NickForm.Meta):
		fields = ['name']

class GroupNickForm(NickForm):
	class Meta(NickForm.Meta):
		fields = ['name', 'abbreviation']

class ScenerAddGroupForm(forms.Form):
	group_name = forms.CharField(widget = forms.TextInput(attrs = {'class': 'group_autocomplete'}))
	# group_id can contain a releaser ID, or 'newgroup' to indicate that a new group
	# should be created with the above name
	group_id = forms.CharField(widget = forms.HiddenInput)

class GroupAddMemberForm(forms.Form):
	scener_name = forms.CharField(widget = forms.TextInput(attrs = {'class': 'scener_autocomplete'}))
	# scener_id can contain a releaser ID, or 'newscener' to indicate that a new scener
	# should be created with the above name
	scener_id = forms.CharField(widget = forms.HiddenInput)

class AttachedNickForm(forms.Form):
	nick_id = forms.CharField(widget = forms.HiddenInput)
	name = forms.CharField(widget = forms.HiddenInput)
	
	def clean(self):
		cleaned_data = self.cleaned_data
		nick_id = cleaned_data.get("nick_id")
		
		if nick_id == 'error':
			raise forms.ValidationError("Name has not been matched to a scener/group")
		
		# Always return the full collection of cleaned data.
		return cleaned_data
	
	def matched_nick(self):
		cleaned_data = self.cleaned_data
		nick_id = cleaned_data.get("nick_id")
		name = cleaned_data.get("name")
		return Nick.from_id_and_name(nick_id, name)

AttachedNickFormSet = formset_factory(AttachedNickForm, extra=0)

class ProductionAddCreditForm(forms.Form):
	nick_name = forms.CharField(label = 'Name', widget = forms.TextInput(attrs = {'class': 'nick_autocomplete'}))
	# nick_id can contain a nick ID, 'newscener' or 'newgroup' as per Nick.from_id_and_name
	nick_id = forms.CharField(widget = forms.HiddenInput)
	role = forms.CharField()

class ReleaserAddCreditForm(forms.Form):
	def __init__(self, releaser, *args, **kwargs):
		super(ReleaserAddCreditForm, self).__init__(*args, **kwargs)
		self.fields['nick_id'] = forms.ModelChoiceField(
			label = 'Credited as',
			queryset = releaser.nicks.order_by('name'),
			initial = releaser.primary_nick.id
		)
		self.fields['production_name'] = forms.CharField(label = 'On production', widget = forms.TextInput(attrs = {'class': 'production_autocomplete'}))
		self.fields['production_id'] = forms.CharField(widget = forms.HiddenInput)
		self.fields['role'] = forms.CharField()
		
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
