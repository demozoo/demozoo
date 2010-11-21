from django import forms
from demoscene.models import Production, ProductionType, Platform, DownloadLink, Nick, Screenshot, Credit
from fuzzy_date_field import FuzzyDateField
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import inlineformset_factory
from nick_field import NickField
from byline_field import BylineField

class ProductionEditCoreDetailsForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(ProductionEditCoreDetailsForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField(initial = self.instance.title)
		self.fields['byline'] = BylineField(required = False, initial = self.instance.byline(), label = 'By')
		self.fields['release_date'] = FuzzyDateField(required = False, initial = self.instance.release_date,
			help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
		
	def save(self, commit = True):
		self.instance.title = self.cleaned_data['title']
		
		# will probably fail if commit = False...
		if self.cleaned_data['byline']:
			self.cleaned_data['byline'].commit(self.instance)
		else:
			self.instance.author_nicks = []
			self.instance.author_affiliation_nicks = []
		
		self.instance.release_date = self.cleaned_data['release_date']
		if commit:
			self.instance.save()
		return self.instance

class MusicEditCoreDetailsForm(ProductionEditCoreDetailsForm):
	def __init__(self, *args, **kwargs):
		super(MusicEditCoreDetailsForm, self).__init__(*args, **kwargs)
		
		try:
			initial_type = self.instance.types.all()[0].id
		except IndexError:
			initial_type = None
		
		self.fields['type'] = ProductionTypeChoiceField(
			queryset = ProductionType.music_types(),
			initial = initial_type
		)
		
	def save(self, *args, **kwargs):
		super(MusicEditCoreDetailsForm, self).save(*args, **kwargs)
		if self.cleaned_data['type']:
			self.instance.types = [ self.cleaned_data['type'] ]
		return self.instance

class GraphicsEditCoreDetailsForm(ProductionEditCoreDetailsForm):
	def __init__(self, *args, **kwargs):
		super(GraphicsEditCoreDetailsForm, self).__init__(*args, **kwargs)
		
		try:
			initial_type = self.instance.types.all()[0].id
		except IndexError:
			initial_type = None
		
		self.fields['type'] = ProductionTypeChoiceField(
			queryset = ProductionType.graphic_types(),
			initial = initial_type
		)
		
	def save(self, *args, **kwargs):
		super(GraphicsEditCoreDetailsForm, self).save(*args, **kwargs)
		if self.cleaned_data['type']:
			self.instance.types = [ self.cleaned_data['type'] ]
		return self.instance

class CreateProductionForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(CreateProductionForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField()
		self.fields['byline'] = BylineField(required = False, label = 'By')
		self.fields['release_date'] = FuzzyDateField(required = False,
			help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
		
	def save(self, commit = True):
		if not commit:
			raise Exception("we don't support saving CreateProductionForm with commit = False. Sorry!")
		
		self.instance.title = self.cleaned_data['title']
		self.instance.release_date = self.cleaned_data['release_date']
		self.instance.save()
		if self.cleaned_data['byline']:
			self.cleaned_data['byline'].commit(self.instance)
		return self.instance

class CreateMusicForm(CreateProductionForm):
	def __init__(self, *args, **kwargs):
		super(CreateMusicForm, self).__init__(*args, **kwargs)
		self.fields['type'] = ProductionTypeChoiceField(
			queryset = ProductionType.music_types(),
			initial = ProductionType.objects.get(internal_name = 'music')
		)
		self.fields['platform'] = forms.ModelChoiceField(required = False, queryset = Platform.objects.all(), empty_label = 'Any')
		
	def save(self, *args, **kwargs):
		super(CreateMusicForm, self).save(*args, **kwargs)
		
		if self.cleaned_data['type']:
			self.instance.types = [ self.cleaned_data['type'] ]
		if self.cleaned_data['platform']:
			self.instance.platforms = [ self.cleaned_data['platform'] ]
		return self.instance

class CreateGraphicsForm(CreateProductionForm):
	def __init__(self, *args, **kwargs):
		super(CreateGraphicsForm, self).__init__(*args, **kwargs)
		self.fields['type'] = ProductionTypeChoiceField(
			queryset = ProductionType.graphic_types(),
			initial = ProductionType.objects.get(internal_name = 'graphics')
		)
		self.fields['platform'] = forms.ModelChoiceField(required = False, queryset = Platform.objects.all(), empty_label = 'Any')
		
	def save(self, *args, **kwargs):
		super(CreateGraphicsForm, self).save(*args, **kwargs)
		
		if self.cleaned_data['type']:
			self.instance.types = [ self.cleaned_data['type'] ]
		if self.cleaned_data['platform']:
			self.instance.platforms = [ self.cleaned_data['platform'] ]
		return self.instance

class ProductionTypeChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return "%s %s" % (u'\u2192' * (obj.depth - 1), obj.name)

class ProductionTypeForm(forms.Form):
	production_type = ProductionTypeChoiceField(queryset = ProductionType.featured_types())

class BaseProductionTypeFormset(BaseFormSet):
	def get_production_types(self):
		prod_types = []
		for prod_type_form in self.forms:
			if hasattr(prod_type_form, 'cleaned_data') and prod_type_form.cleaned_data.get('production_type'):
				prod_types.append(prod_type_form.cleaned_data['production_type'])
		for prod_type_form in self.deleted_forms:
			if hasattr(prod_type_form, 'cleaned_data') and prod_type_form.cleaned_data.get('production_type') and prod_type_form.cleaned_data['production_type'] in prod_types:
				prod_types.remove(prod_type_form.cleaned_data['production_type'])
		return prod_types

ProductionTypeFormSet = formset_factory(ProductionTypeForm, can_delete = True, formset = BaseProductionTypeFormset)

class ProductionPlatformForm(forms.Form):
	platform = forms.ModelChoiceField(queryset = Platform.objects.order_by('name'))

class BaseProductionPlatformFormSet(BaseFormSet):
	def get_production_platforms(self):
		platforms = []
		for prod_platform_form in self.forms:
			if hasattr(prod_platform_form, 'cleaned_data') and prod_platform_form.cleaned_data.get('platform'):
				platforms.append(prod_platform_form.cleaned_data['platform'])
		for prod_platform_form in self.deleted_forms:
			if hasattr(prod_platform_form, 'cleaned_data') and prod_platform_form.cleaned_data.get('platform') and prod_platform_form.cleaned_data['platform'] in platforms:
				platforms.remove(prod_platform_form.cleaned_data['platform'])
		return platforms

ProductionPlatformFormSet = formset_factory(ProductionPlatformForm, can_delete = True, formset = BaseProductionPlatformFormSet)

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

