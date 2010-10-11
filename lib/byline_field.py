from django import forms
from demoscene.models import Byline
from submit_button_field import SubmitButtonInput
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from matched_nick_field import MatchedNickField, NickSelection
import re

# An object which encapsulates the state of a BylineWidget as derived from its posted data;
# this is what BylineWidget returns from value_from_datadict
class BylineLookup():
	def __init__(self,
		search_term = '', autoaccept = False,
		author_nick_selections = [], affiliation_nick_selections = []):
		
		self.search_term = search_term # the byline string
		self.autoaccept = autoaccept # whether we should continue upon successfully resolving
			# all byline components, as opposed to re-showing the form
		self.author_nick_selections = author_nick_selections
		self.affiliation_nick_selections = affiliation_nick_selections
		
		# parse the byline
		parts = self.search_term.split('/')
		authors_string = parts[0] # everything before first slash is an author
		affiliations_string = '^'.join(parts[1:]) # everything after first slash is an affiliation
		author_names = re.split(r"[\,\+\^\&]", authors_string)
		self.author_names = [name.strip() for name in author_names]
		affiliation_names = re.split(r"[\,\+\^\&]", affiliations_string)
		self.affiliation_names = [name.strip() for name in affiliation_names if name.strip()]
		
		# create MatchedNickFields from the components
		self.author_matched_nick_fields = [
			MatchedNickField(author_name, None, group_names = self.affiliation_names)
			for author_name in self.author_names
		]
		self.affiliation_matched_nick_fields = [
			MatchedNickField(affiliation_name, None, groups_only = True, member_names = self.author_names)
			for affiliation_name in self.affiliation_names
		]
	
	def render_match_fields(self, name, attrs = {}):
		match_html_output = []
		
		for i, field in enumerate(self.author_matched_nick_fields):
			try:
				value = self.author_nick_selections[i]
			except IndexError:
				value = None
			field_name = name + ('_author_match_%s' % i)
			html = field.widget.render(field_name, value, attrs = attrs)
			match_html_output.append(html)
		
		for i, field in enumerate(self.affiliation_matched_nick_fields):
			try:
				value = self.affiliation_nick_selections[i]
			except IndexError:
				value = None
			field_name = name + ('_affiliation_match_%s' % i)
			html = field.widget.render(field_name, value, attrs = attrs)
			match_html_output.append(html)
		
		return u''.join(match_html_output)
	
	@staticmethod
	def from_value(value):
		# value can be:
		# a Byline
		# None
		# an existing BylineLookup
		if not value:
			return BylineLookup()
		elif isinstance(value, BylineLookup):
			return BylineLookup(
				search_term = value.search_term,
				autoaccept = value.autoaccept,
				author_nick_selections = value.author_nick_selections,
				affiliation_nick_selections = value.affiliation_nick_selections)
		elif isinstance(value, Byline):
			return BylineLookup(
				search_term = value.__unicode__(),
				author_nick_selections = [NickSelection(nick.id, nick.name) for nick in value.author_nicks],
				affiliation_nick_selections = [NickSelection(nick.id, nick.name) for nick in value.affiliation_nicks])
		else:
			raise Exception("Don't know how to handle %s as a byline lookup" % repr(value))

class BylineWidget(forms.Widget):
	def __init__(self, attrs = None):
		self.search_widget = forms.TextInput(attrs = attrs)
		self.lookup_widget = SubmitButtonInput(button_text = 'Find names')
		super(BylineWidget, self).__init__(attrs = attrs)
	
	def value_from_datadict(self, data, files, name):
		search_term = self.search_widget.value_from_datadict(data, files, name + '_search')
		if not search_term:
			return None
		
		explicit_lookup_requested = self.lookup_widget.value_from_datadict(data, files, name + '_lookup')
		
		byline_lookup = BylineLookup(
			search_term = search_term,
			autoaccept = not explicit_lookup_requested)
		
		if not explicit_lookup_requested:
			byline_lookup.author_nick_selections = [
				field.widget.value_from_datadict(data, files, name + ('_author_match_%s' % i))
				for i, field in enumerate(byline_lookup.author_matched_nick_fields)
			]
			byline_lookup.affiliation_nick_selections = [
				field.widget.value_from_datadict(data, files, name + ('_affiliation_match_%s' % i))
				for i, field in enumerate(byline_lookup.affiliation_matched_nick_fields)
			]
		return byline_lookup
	
	def id_for_label(self, id_):
		if id_:
			id_ += '_search'
		return id_
	id_for_label = classmethod(id_for_label)
	
	def render(self, name, value, attrs=None):
		byline_lookup = BylineLookup.from_value(value)
		
		search_html_output = [
			self.search_widget.render(name + '_search', byline_lookup.search_term, attrs = attrs),
			self.lookup_widget.render(name + '_lookup', None, attrs = attrs)
		]
		
		if byline_lookup.search_term:
			matched_nick_html = byline_lookup.render_match_fields(name)
		else:
			matched_nick_html = ''
		
		output = [
			u'<div class="byline_search">' + u''.join(search_html_output) + u'</div>',
			u'<div class="byline_match_container">' + matched_nick_html + u'</div>'
		]
		
		root_classname = u'byline_field'
		return mark_safe(u'<div class="' + root_classname + u'">' + u''.join(output) + u'</div>')
		
class BylineField(forms.Field):
	def __init__(self, *args, **kwargs):
		self.widget = BylineWidget()
		super(BylineField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			# pass on to Field to handle null value according to the 'blank' parameter
			return super(BylineField, self).clean(value)
		else:
			byline_lookup = BylineLookup.from_value(value)
			
			clean_author_nick_selections = []
			clean_affiliation_nick_selections = []
			if byline_lookup.autoaccept:
				validation_message = "Not all names could be matched to a scener or group; please select the appropriate ones from the lists."
			else:
				validation_message = "Please select the appropriate sceners / groups from the lists."
			
			for i, field in enumerate(byline_lookup.author_matched_nick_fields):
				try:
					value = byline_lookup.author_nick_selections[i]
				except IndexError:
					raise ValidationError(validation_message)
				clean_value = field.clean(value)
				if not clean_value:
					raise ValidationError(validation_message)
				clean_author_nick_selections.append(clean_value)
			
			for i, field in enumerate(byline_lookup.affiliation_matched_nick_fields):
				try:
					value = byline_lookup.affiliation_nick_selections[i]
				except IndexError:
					raise ValidationError(validation_message)
				clean_value = field.clean(value)
				if not clean_value:
					raise ValidationError(validation_message)
				clean_affiliation_nick_selections.append(clean_value)
			
			return Byline(
				clean_author_nick_selections, clean_affiliation_nick_selections)

# test stuff

class ProdAuthorForm(forms.Form):
	byline = BylineField(label = 'By')

from demoscene.models import *
bb = Production.objects.get(id = 30)

initial_prod_form = ProdAuthorForm()
edit_prod_form = ProdAuthorForm(initial = {'byline': bb.byline()})
