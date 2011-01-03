from django import forms
from django.forms.models import formset_factory, BaseModelFormSet
from demoscene.models import Party, PartySeries, Competition, CompetitionPlacing
from any_format_date_field import AnyFormatDateField
from production_field import ProductionField
from form_with_location import ModelFormWithLocation

class PartyForm(ModelFormWithLocation):
	existing_party_series = forms.ModelChoiceField(label = 'Party series', queryset = PartySeries.objects.order_by('name'), required = False)
	new_party_series_name = forms.CharField(label = '- or, add a new one', required = False)
	name = forms.CharField(label = 'Party name')
	start_date = AnyFormatDateField()
	end_date = AnyFormatDateField()
	class Meta:
		model = Party
		fields = ('existing_party_series', 'new_party_series_name', 'start_date', 'end_date', 'name', 'tagline', 'location')

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

class PartySeriesEditNotesForm(forms.ModelForm):
	class Meta:
		model = PartySeries
		fields = ['notes']

class CompetitionForm(forms.ModelForm):
	class Meta:
		model = Competition
		fields = ('name',)

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
