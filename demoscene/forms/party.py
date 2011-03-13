from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet
from demoscene.models import Party, PartySeries, Competition, CompetitionPlacing, Platform, ProductionType
from any_format_date_field import AnyFormatDateField
from production_field import ProductionField
from byline_field import BylineField
from form_with_location import ModelFormWithLocation

class PartyForm(ModelFormWithLocation):
	name = forms.CharField(label = 'Party name', help_text = "e.g. Revision 2011")
	start_date = AnyFormatDateField()
	end_date = AnyFormatDateField()
	party_series_name = forms.CharField(label = 'Party series', help_text = "e.g. Revision")
	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location', 'party_series_name')

class EditPartyForm(ModelFormWithLocation):
	start_date = AnyFormatDateField()
	end_date = AnyFormatDateField()
	class Meta:
		model = Party
		fields = ('name', 'start_date', 'end_date', 'tagline', 'location')

class PartyEditNotesForm(forms.ModelForm):
	class Meta:
		model = Party
		fields = ['notes']

class PartyEditExternalLinksForm(forms.ModelForm):
	class Meta:
		model = Party
		fields = Party.external_site_ref_field_names + ['pouet_party_when']
		widgets = {
			'twitter_username': forms.TextInput(attrs={'class': 'numeric'}), # not really numeric, but box is the same size
			'demoparty_net_url_fragment': forms.TextInput(attrs={'class': 'numeric'}), # not really numeric, but box is the same size
			'slengpung_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'pouet_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'pouet_party_when': forms.TextInput(attrs={'class': 'numeric'}),
			'bitworld_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'csdb_party_id': forms.TextInput(attrs={'class': 'numeric'}),
			'bitjam_author_id': forms.TextInput(attrs={'class': 'numeric'}),
			'breaks_amiga_party_id': forms.TextInput(attrs={'class': 'numeric'}),
		}

class EditPartySeriesForm(forms.ModelForm):
	class Meta:
		model = PartySeries
		fields = ('name', 'website', 'twitter_username', 'pouet_party_id')
		widgets = {
			'twitter_username': forms.TextInput(attrs={'class': 'numeric'}), # not really numeric, but box is the same size
			'pouet_party_id': forms.TextInput(attrs={'class': 'numeric'}),
		}

class PartySeriesEditNotesForm(forms.ModelForm):
	class Meta:
		model = PartySeries
		fields = ['notes']

class CompetitionForm(forms.ModelForm):
	class Meta:
		model = Competition
		fields = ('name',)

class CompetitionResultForm(forms.Form):
	placing = forms.CharField(required = False)
	title = forms.CharField()
	byline = BylineField(required = False)
	platform = forms.ModelChoiceField(required = False, queryset = Platform.objects.all())
	production_type = forms.ModelChoiceField(required = False, queryset = ProductionType.objects.all())
	score = forms.CharField(required = False)

CompetitionResultFormSet = formset_factory(CompetitionResultForm)

class CompetitionPlacingForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', CompetitionPlacing())
		super(CompetitionPlacingForm, self).__init__(*args, **kwargs)
		self.fields['ranking'] = forms.CharField(
			initial = self.instance.ranking,
			required = False,
			widget = forms.TextInput(attrs = {'class': 'numeric'}))
		self.fields['production'] = ProductionField(
			initial = self.instance.production_id,
			show_production_type_field = True,
		)
		self.fields['score'] = forms.CharField(
			initial = self.instance.score,
			required = False,
			widget = forms.TextInput(attrs = {'class': 'numeric'}))
		
	def save(self, commit = True):
		if not commit:
			raise Exception("we don't support saving CompetitionPlacingForm with commit = False. Sorry!")
		
		self.instance.ranking = self.cleaned_data['ranking']
		self.instance.production = self.cleaned_data['production'].commit()
		self.instance.score = self.cleaned_data['score']
		self.instance.save()
		return self.instance

	def has_changed(self):
		return True # force all objects to be saved so that ordering (done out of form) takes effect

class BaseCompetitionPlacingFormSet(BaseModelFormSet):
	def __init__(self, data=None, files=None, instance=None, prefix=None):
		self.model = CompetitionPlacing
		if instance is None:
			self.instance = Competition()
		else:
			self.instance = instance
		qs = self.instance.placings.order_by('position')
		super(BaseCompetitionPlacingFormSet, self).__init__(data, files, prefix=prefix, queryset=qs)
	
	def validate_unique(self):
		# CompetitionPlacingForm has no unique constraints,
		# so don't try to rummage around in its non-existent metaclass to find some
		return
		
	def _construct_form(self, i, **kwargs):
		# ensure foreign key to competition is set
		form = super(BaseCompetitionPlacingFormSet, self)._construct_form(i, **kwargs)
		form.instance.competition = self.instance
		return form

CompetitionPlacingFormset = formset_factory(CompetitionPlacingForm,
	formset = BaseCompetitionPlacingFormSet,
	can_delete = True, can_order = True, extra=1 )
CompetitionPlacingFormset.fk = [f for f in CompetitionPlacing._meta.fields if f.name == 'competition'][0]
