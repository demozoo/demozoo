from django import forms
from demoscene.models import Production, ProductionType, Platform, Releaser, DownloadLink, Nick
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, modelformset_factory

class ProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', )
		
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
		fields = ('name', )

class ScenerForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name', )

class NickForm(forms.ModelForm):
	nick_variant_list = forms.CharField(label = "Alternative spellings / abbreviations", required = False)
	
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
	# group_id can contain a releaser ID, or 'new' to indicate that a new group
	# should be created with the above name
	group_id = forms.CharField(widget = forms.HiddenInput)

class GroupAddMemberForm(forms.Form):
	scener_name = forms.CharField(widget = forms.TextInput(attrs = {'class': 'scener_autocomplete'}))
	# scener_id can contain a releaser ID, or 'new' to indicate that a new scener
	# should be created with the above name
	scener_id = forms.CharField(widget = forms.HiddenInput)
