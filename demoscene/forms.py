from django import forms
from demoscene.models import Production, ProductionType, Platform, Releaser, DownloadLink, Nick
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, modelformset_factory

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


class GroupForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('',)

class AdminGroupForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('notes',)

class ScenerForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ()

class AdminScenerForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('notes',)

class NickForm(forms.ModelForm):
	nick_variant_list = forms.CharField(label = "Other spellings / abbreviations of this name", required = False)
	
	def __init__(self, *args, **kwargs):
		super(NickForm, self).__init__(*args, **kwargs)
		if kwargs.has_key('instance'):
			instance = kwargs['instance']
			self.initial['nick_variant_list'] = instance.nick_variant_list
	
	def save(self, commit = True):
		instance = super(NickForm, self).save(commit=False)
		instance.nick_variant_list = self.cleaned_data['nick_variant_list']
		if commit:
			instance.save()
		return instance
	
	class Meta:
		model = Nick
		fields = ('name', )

NickFormSet = modelformset_factory(Nick, can_delete = True, form = NickForm)

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
		