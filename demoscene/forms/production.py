from django import forms
from demoscene.models import Production, ProductionType, Platform, DownloadLink, Nick, Screenshot, Credit
from fuzzy_date_field import FuzzyDateField
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from nick_field import NickField
from byline_field import BylineField

class ProductionEditCoreDetailsForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(ProductionEditCoreDetailsForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField(initial = self.instance.title)
		self.fields['byline'] = BylineField(initial = self.instance.byline(), label = 'By')
		self.fields['release_date'] = FuzzyDateField(required = False, initial = self.instance.release_date,
			help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
		
	def save(self, commit = True):
		self.instance.title = self.cleaned_data['title']
		
		# will probably fail if commit = False...
		self.cleaned_data['byline'].commit(self.instance)
		
		self.instance.release_date = self.cleaned_data['release_date']
		if commit:
			self.instance.save()
		return self.instance

class CreateProductionForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(CreateProductionForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField()
		self.fields['byline'] = BylineField(label = 'By')
		self.fields['release_date'] = FuzzyDateField(required = False,
			help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
		
	def save(self, commit = True):
		if not commit:
			raise Exception("we don't support saving CreateProductionForm with commit = False. Sorry!")
		
		self.instance.title = self.cleaned_data['title']
		self.instance.save()
		self.instance.release_date = self.cleaned_data['release_date']
		self.cleaned_data['byline'].commit(self.instance)
		return self.instance

class ProductionTypeForm(forms.Form):
	production_type = forms.ModelChoiceField(queryset = ProductionType.objects.order_by('name'))

ProductionTypeFormSet = formset_factory(ProductionTypeForm, can_delete = True)

class ProductionPlatformForm(forms.Form):
	platform = forms.ModelChoiceField(queryset = Platform.objects.order_by('name'))

ProductionPlatformFormSet = formset_factory(ProductionPlatformForm, can_delete = True)

DownloadLinkFormSet = inlineformset_factory(Production, DownloadLink, extra=1)

class ProductionEditNotesForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = ['notes']

class ProductionDownloadLinkForm(forms.ModelForm):
	class Meta:
		model = DownloadLink
		fields = ['url']

class ProductionEditExternalLinksForm(forms.ModelForm):
	class Meta:
		model = Production
		fields = Production.external_site_ref_field_names
		widgets = {
			'pouet_id': forms.TextInput(attrs={'class': 'numeric'}),
			'csdb_id': forms.TextInput(attrs={'class': 'numeric'}),
			'bitworld_id': forms.TextInput(attrs={'class': 'numeric'}),
		}

class ProductionCreditForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Credit())
		super(ProductionCreditForm, self).__init__(*args, **kwargs)
		try:
			nick = self.instance.nick
			self.fields['nick'] = NickField(initial = nick)
		except Nick.DoesNotExist:
			self.fields['nick'] = NickField()
		self.fields['role'] = forms.CharField(initial = self.instance.role)
	
	def save(self, commit = True):
		self.instance.role = self.cleaned_data['role']
		self.instance.nick = self.cleaned_data['nick'].commit()
		if commit:
			self.instance.save()
		return self.instance

class ProductionAddScreenshotForm(forms.ModelForm):
	class Meta:
		model = Screenshot
		fields = ['original']

ProductionAddScreenshotFormset = formset_factory(ProductionAddScreenshotForm, extra=6)

