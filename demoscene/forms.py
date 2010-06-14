from django import forms
from demoscene.models import Production, ProductionType, Platform, Releaser, DownloadLink
from django.forms.models import inlineformset_factory

class ProductionForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ('title', )
		
class ProductionTypeForm(forms.Form):
	production_type = forms.ModelChoiceField(queryset = ProductionType.objects.order_by('name'))

ProductionTypeFormSet = forms.formsets.formset_factory(ProductionTypeForm, can_delete = True)

class ProductionPlatformForm(forms.Form):
	platform = forms.ModelChoiceField(queryset = Platform.objects.order_by('name'))

ProductionPlatformFormSet = forms.formsets.formset_factory(ProductionPlatformForm, can_delete = True)

DownloadLinkFormSet = inlineformset_factory(Production, DownloadLink, extra=1)


class GroupForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name', )


class ScenerForm(forms.ModelForm):
	class Meta:
		model = Releaser
		fields = ('name', )

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
