from django import forms
from demoscene.models import Production, ProductionType, Platform, SoundtrackLink, ProductionLink, Edit
from fuzzy_date_field import FuzzyDateField
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, BaseModelFormSet
from nick_field import NickField
from byline_field import BylineField
from production_field import ProductionField
from production_type_field import ProductionTypeChoiceField, ProductionTypeMultipleChoiceField
from demoscene.forms.common import ExternalLinkForm, BaseExternalLinkFormSet


def readable_list(list):
	if len(list) == 0:
		return "none"
	else:
		return u", ".join([unicode(item) for item in list])


class BaseProductionEditCoreDetailsForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(BaseProductionEditCoreDetailsForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField(initial=self.instance.title)
		self.fields['byline'] = BylineField(required=False, initial=self.instance.byline_search(), label='By')
		self.fields['release_date'] = FuzzyDateField(required=False, initial=self.instance.release_date,
			help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")')
		self.fields['platforms'] = forms.ModelMultipleChoiceField(required=False, label='Platform',
			initial=[platform.id for platform in self.instance.platforms.all()],
			queryset=Platform.objects.all())

	def save(self, commit=True):
		self.instance.title = self.cleaned_data['title']

		# will probably fail if commit = False...
		if self.cleaned_data['byline']:
			self.cleaned_data['byline'].commit(self.instance)
		else:
			self.instance.author_nicks = []
			self.instance.author_affiliation_nicks = []
		self.unparsed_byline = None

		self.instance.platforms = self.cleaned_data['platforms']
		self.instance.release_date = self.cleaned_data['release_date']
		if commit:
			self.instance.save()
		return self.instance

	@property
	def changed_data_description(self):
		descriptions = []
		changed_fields = self.changed_data
		if 'title' in changed_fields:
			descriptions.append(u"title to '%s'" % self.cleaned_data['title'])
		if 'byline' in changed_fields:
			descriptions.append(u"author to '%s'" % self.cleaned_data['byline'])
		if 'release_date' in changed_fields:
			descriptions.append(u"release date to %s" % self.cleaned_data['release_date'])
		if 'type' in changed_fields:
			descriptions.append(u"type to %s" % self.cleaned_data['type'])
		if 'types' in changed_fields:
			if len(self.cleaned_data['types']) > 1:
				descriptions.append(u"types to %s" % readable_list(self.cleaned_data['types']))
			else:
				descriptions.append(u"type to %s" % readable_list(self.cleaned_data['types']))
		if 'platform' in changed_fields:
			descriptions.append(u"platform to %s" % self.cleaned_data['platform'])
		if 'platforms' in changed_fields:
			if len(self.cleaned_data['platforms']) > 1:
				descriptions.append(u"platforms to %s" % readable_list(self.cleaned_data['platforms']))
			else:
				descriptions.append(u"platform to %s" % readable_list(self.cleaned_data['platforms']))
		if descriptions:
			return u"Set %s" % (u", ".join(descriptions))

	def log_edit(self, user):
		description = self.changed_data_description
		if description:
			Edit.objects.create(action_type='edit_production_core_details', focus=self.instance,
				description=description, user=user)


class ProductionEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
	# has multiple types
	def __init__(self, *args, **kwargs):
		super(ProductionEditCoreDetailsForm, self).__init__(*args, **kwargs)
		self.fields['types'] = ProductionTypeMultipleChoiceField(required=False, label='Type',
			initial=[typ.id for typ in self.instance.types.all()],
			queryset=ProductionType.featured_types())

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
			queryset=ProductionType.music_types(),
			initial=initial_type
		)

	def save(self, *args, **kwargs):
		super(MusicEditCoreDetailsForm, self).save(*args, **kwargs)
		if self.cleaned_data['type']:
			self.instance.types = [self.cleaned_data['type']]
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
			queryset=ProductionType.graphic_types(),
			initial=initial_type
		)

	def save(self, *args, **kwargs):
		super(GraphicsEditCoreDetailsForm, self).save(*args, **kwargs)
		if self.cleaned_data['type']:
			self.instance.types = [self.cleaned_data['type']]
		return self.instance


class CreateProductionForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', Production())
		super(CreateProductionForm, self).__init__(*args, **kwargs)
		self.fields['title'] = forms.CharField()
		self.fields['byline'] = BylineField(required=False, label='By')
		self.fields['release_date'] = FuzzyDateField(required=False,
			help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")')
		self.fields['types'] = ProductionTypeMultipleChoiceField(required=False, label='Type',
			queryset=ProductionType.featured_types())
		self.fields['platforms'] = forms.ModelMultipleChoiceField(required=False, label='Platform',
			queryset=Platform.objects.all())

	def save(self, commit=True):
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

	def log_creation(self, user):
		Edit.objects.create(action_type='create_production', focus=self.instance,
			description=(u"Added production '%s'" % self.instance.title), user=user)


class CreateMusicForm(CreateProductionForm):
	def __init__(self, *args, **kwargs):
		super(CreateMusicForm, self).__init__(*args, **kwargs)
		self.fields['type'] = ProductionTypeChoiceField(
			queryset=ProductionType.music_types(),
			initial=ProductionType.objects.get(internal_name='music')
		)
		self.fields['platform'] = forms.ModelChoiceField(required=False, queryset=Platform.objects.all(), empty_label='Any')

	def save(self, *args, **kwargs):
		self.instance.supertype = 'music'
		super(CreateMusicForm, self).save(*args, **kwargs)

		if self.cleaned_data['type']:
			self.instance.types = [self.cleaned_data['type']]
		if self.cleaned_data['platform']:
			self.instance.platforms = [self.cleaned_data['platform']]
		return self.instance


class CreateGraphicsForm(CreateProductionForm):
	def __init__(self, *args, **kwargs):
		super(CreateGraphicsForm, self).__init__(*args, **kwargs)
		self.fields['type'] = ProductionTypeChoiceField(
			queryset=ProductionType.graphic_types(),
			initial=ProductionType.objects.get(internal_name='graphics')
		)
		self.fields['platform'] = forms.ModelChoiceField(required=False, queryset=Platform.objects.all(), empty_label='Any')

	def save(self, *args, **kwargs):
		self.instance.supertype = 'graphics'
		super(CreateGraphicsForm, self).save(*args, **kwargs)

		if self.cleaned_data['type']:
			self.instance.types = [self.cleaned_data['type']]
		if self.cleaned_data['platform']:
			self.instance.platforms = [self.cleaned_data['platform']]
		return self.instance


class ProductionEditNotesForm(forms.ModelForm):
	def log_edit(self, user):
		Edit.objects.create(action_type='edit_production_notes', focus=self.instance,
			description="Edited notes", user=user)

	class Meta:
		model = Production
		fields = ['notes']


class ProductionDownloadLinkForm(ExternalLinkForm):
	def save(self, commit=True):
		instance = super(ProductionDownloadLinkForm, self).save(commit=False)
		instance.is_download_link = True
		if commit:
			instance.save()
		return instance

	class Meta:
		model = ProductionLink
		fields = []

ProductionDownloadLinkFormSet = inlineformset_factory(Production, ProductionLink,
	form=ProductionDownloadLinkForm, formset=BaseExternalLinkFormSet, extra=1)


class ProductionExternalLinkForm(ExternalLinkForm):
	class Meta:
		model = ProductionLink
		fields = []

ProductionExternalLinkFormSet = inlineformset_factory(Production, ProductionLink,
	form=ProductionExternalLinkForm, formset=BaseExternalLinkFormSet)


class ProductionCreditedNickForm(forms.Form):
	def __init__(self, *args, **kwargs):
		nick = kwargs.pop('nick', None)
		super(ProductionCreditedNickForm, self).__init__(*args, **kwargs)
		if nick:
			self.fields['nick'] = NickField(initial=nick)
		else:
			self.fields['nick'] = NickField()


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
			initial=self.instance.soundtrack_id,
			supertype='music',
			types_to_set=[ProductionType.objects.get(internal_name='music')],
		)

	def save(self, commit=True):
		if not commit:
			raise Exception("we don't support saving SoundtrackLinkForm with commit = False. Sorry!")

		self.instance.soundtrack = self.cleaned_data['soundtrack'].commit()
		self.instance.save()
		return self.instance

	def has_changed(self):
		return True  # force all objects to be saved so that ordering (done out of form) takes effect


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
	formset=BaseProductionSoundtrackLinkFormSet,
	can_delete=True, can_order=True, extra=1)
ProductionSoundtrackLinkFormset.fk = [f for f in SoundtrackLink._meta.fields if f.name == 'production'][0]
