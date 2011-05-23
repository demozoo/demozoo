from django import forms
from demoscene.models import Production, ProductionType, Platform, DownloadLink, Nick, Screenshot, Credit, SoundtrackLink
from fuzzy_date_field import FuzzyDateField
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import inlineformset_factory, BaseModelFormSet
from nick_field import NickField
from byline_field import BylineField
from production_field import ProductionField
from production_type_field import ProductionTypeChoiceField, ProductionTypeMultipleChoiceField

class BaseProductionEditCoreDetailsForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(BaseProductionEditCoreDetailsForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField(initial = self.instance.title)
		self.fields['byline'] = BylineField(required = False, initial = self.instance.byline(), label = 'By')
		self.fields['release_date'] = FuzzyDateField(required = False, initial = self.instance.release_date,
			help_text = '(As accurately as you know it - e.g. "1996", "Mar 2010")')
		self.fields['platforms'] = forms.ModelMultipleChoiceField(required = False, label = 'Platform',
			initial = [platform.id for platform in self.instance.platforms.all()], queryset = Platform.objects.all())
		
	def save(self, commit = True):
		self.instance.title = self.cleaned_data['title']
		
		# will probably fail if commit = False...
		if self.cleaned_data['byline']:
			self.cleaned_data['byline'].commit(self.instance)
		else:
			self.instance.author_nicks = []
			self.instance.author_affiliation_nicks = []
		
		self.instance.platforms = self.cleaned_data['platforms']
		self.instance.release_date = self.cleaned_data['release_date']
		if commit:
			self.instance.save()
		return self.instance

class ProductionEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
	# has multiple types
	def __init__(self, *args, **kwargs):
		super(ProductionEditCoreDetailsForm, self).__init__(*args, **kwargs)
		self.fields['types'] = ProductionTypeMultipleChoiceField(required = False, label = 'Type',
			initial = [typ.id for typ in self.instance.types.all()], queryset = ProductionType.featured_types())
		
		self.has_multiple_types = True
		
	def save(self, *args, **kwargs):
		super(ProductionEditCoreDetailsForm, self).save(*args, **kwargs)
		self.instance.types = self.cleaned_data['types']

class MusicEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
	def __init__(self, *args, **kwargs):
		super(MusicEditCoreDetailsForm, self).__init__(*args, **kwargs)
		
		self.has_multiple_types = False
		
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

class GraphicsEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
	def __init__(self, *args, **kwargs):
		super(GraphicsEditCoreDetailsForm, self).__init__(*args, **kwargs)
		
		self.has_multiple_types = False
		
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
		self.fields['types'] = ProductionTypeMultipleChoiceField(required = False, label = 'Type',
			queryset = ProductionType.featured_types())
		self.fields['platforms'] = forms.ModelMultipleChoiceField(required = False, label = 'Platform',
			queryset = Platform.objects.all())
		
	def save(self, commit = True):
		if not commit:
			raise Exception("we don't support saving CreateProductionForm with commit = False. Sorry!")
		
		if not self.instance.supertype:
			self.instance.supertype = 'production'
		self.instance.title = self.cleaned_data['title']
		self.instance.release_date = self.cleaned_data['release_date']
		self.instance.save()
		if self.cleaned_data['byline']:
			self.cleaned_data['byline'].commit(self.instance)
		self.instance.types = self.cleaned_data['types']
		self.instance.platforms = self.cleaned_data['platforms']
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
		self.instance.supertype = 'music'
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
		self.instance.supertype = 'graphics'
		super(CreateGraphicsForm, self).save(*args, **kwargs)
		
		if self.cleaned_data['type']:
			self.instance.types = [ self.cleaned_data['type'] ]
		if self.cleaned_data['platform']:
			self.instance.platforms = [ self.cleaned_data['platform'] ]
		return self.instance

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

# An individual form row in the 'edit soundtrack details' form.
# Even though this corresponds to a SoundtrackLink object, this can't be a ModelForm
# because ModelForm internals would attempt to create an instance of SoundtrackLink
# immediately upon validation;
# - which we can't do because self.cleaned_data['soundtrack'] is a ProductionSelection,
# not a Production;
# - we can't use Production because that would require us to commit the production to
# the database immediately, which we may not want to do (e.g. if validation elsewhere fails)
# - and we can't use an unsaved Production object there because it has dependent relations.
class SoundtrackLinkForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', SoundtrackLink())
		super(SoundtrackLinkForm, self).__init__(*args, **kwargs)
		self.fields['soundtrack'] = ProductionField(
			initial = self.instance.soundtrack_id,
			supertype = 'music',
			types_to_set = [ProductionType.objects.get(internal_name = 'music')],
		)
		
	def save(self, commit = True):
		if not commit:
			raise Exception("we don't support saving SoundtrackLinkForm with commit = False. Sorry!")
		
		self.instance.soundtrack = self.cleaned_data['soundtrack'].commit()
		self.instance.save()
		return self.instance

	def has_changed(self):
		return True # force all objects to be saved so that ordering (done out of form) takes effect

# A base formset class dedicated to the 'edit soundtrack details' formset, which
# behaves mostly like a ModelFormSet but needs several methods of BaseModelFormSet
# to be monkeypatched to cope with SoundtrackLinkForm not being a true ModelForm
class BaseProductionSoundtrackLinkFormSet(BaseModelFormSet):
	def __init__(self, data=None, files=None, instance=None, prefix=None):
		self.model = SoundtrackLink
		if instance is None:
			self.instance = Production()
		else:
			self.instance = instance
		qs = self.instance.soundtrack_links.order_by('position')
		super(BaseProductionSoundtrackLinkFormSet, self).__init__(data, files, prefix=prefix, queryset=qs)
	
	def validate_unique(self):
		# SoundtrackLinkForm has no unique constraints,
		# so don't try to rummage around in its non-existent metaclass to find some
		return
		
	def _construct_form(self, i, **kwargs):
		# ensure foreign key to production is set
		form = super(BaseProductionSoundtrackLinkFormSet, self)._construct_form(i, **kwargs)
		form.instance.production = self.instance
		return form

ProductionSoundtrackLinkFormset = formset_factory(SoundtrackLinkForm,
	formset = BaseProductionSoundtrackLinkFormSet,
	can_delete = True, can_order = True, extra=1 )
ProductionSoundtrackLinkFormset.fk = [f for f in SoundtrackLink._meta.fields if f.name == 'production'][0]
