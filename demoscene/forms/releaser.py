from django import forms
from django.core.exceptions import ValidationError

from demoscene.models import Releaser, Nick
from form_with_location import ModelFormWithLocation
from nick_field import NickField

class CreateGroupForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name',)

class CreateScenerForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name',)

class ScenerEditLocationForm(ModelFormWithLocation):
	class Meta:
		model = Releaser
		fields = ('location',)

class ScenerEditRealNameForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ['first_name', 'show_first_name', 'surname', 'show_surname', 'real_name_note']
		widgets = {
		    'real_name_note': forms.Textarea(attrs={'class': 'short_notes'}),
		}

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
			'asciiarena_author_id': forms.TextInput(attrs={'class': 'numeric'}), # not actually numeric, but input box is the same size
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
				label = "Use this as their preferred name, instead of '%s'" % releaser.name,
				required = False)
	
	# override validate_unique so that we include the releaser test in unique_together validation;
	# see http://stackoverflow.com/questions/2141030/djangos-modelform-unique-together-validation/3757871#3757871
	def validate_unique(self):
		exclude = self._get_validation_exclusions()
		exclude.remove('releaser') # allow checking against the missing attribute
		try:
			self.instance.validate_unique(exclude=exclude)
		except ValidationError, e:
			self._update_errors({'__all__': [u'This nick cannot be added, as it duplicates an existing one.']})
		
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

class ScenerMembershipForm(forms.Form):
	group_nick = NickField(groups_only = True, label = 'Group name')
	is_current = forms.BooleanField(required = False, label = 'Current member?', initial = True)

class GroupMembershipForm(forms.Form):
	scener_nick = NickField(sceners_only = True, label = 'Scener name')
	is_current = forms.BooleanField(required = False, label = 'Current member?', initial = True)

class GroupSubgroupForm(forms.Form):
	subgroup_nick = NickField(groups_only = True, label = 'Subgroup name')
	is_current = forms.BooleanField(required = False, label = 'Current subgroup?', initial = True)

class EditMembershipForm(forms.Form):
	is_current = forms.BooleanField(required = False, label = 'Current member?', initial = True)

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
