from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from demoscene.models import Nick
from submit_button_field import SubmitButtonInput
from matched_nick_field import MatchedNickField, NickSelection

# An object which encapsulates the state of a NickWidget as derived from its posted data;
# this is what NickWidget returns from value_from_datadict
class NickLookup():
	def __init__(self,
		search_term = None, autoaccept = False,
		nick_selection = None,
		matched_nick_options = {}):
		# valid matched_nick_options include sceners_only, groups_only
		
		self.search_term = search_term # the search term being looked up
		self.autoaccept = autoaccept # whether we should continue upon successfully resolving a nick,
			# as opposed to re-showing the form
		self.nick_selection = nick_selection
		self.matched_nick_field = MatchedNickField(search_term, None,
			**matched_nick_options)
	
	@staticmethod
	def from_value(value, matched_nick_options = {}):
		# value can be:
		# a Nick
		# None
		# an existing NickLookup
		if not value:
			return NickLookup(matched_nick_options = matched_nick_options)
		elif isinstance(value, NickLookup):
			return NickLookup(
				search_term = value.search_term,
				autoaccept = value.autoaccept,
				nick_selection = value.nick_selection,
				matched_nick_options = matched_nick_options)
		elif isinstance(value, Nick):
			return NickLookup(
				search_term = value.name,
				nick_selection = NickSelection(value.id, value.name),
				matched_nick_options = matched_nick_options)
		else:
			raise Exception("Don't know how to handle %s as a nick lookup" % repr(value))

class NickWidget(forms.Widget):
	def __init__(self, attrs = None, matched_nick_options = {}):
		self.matched_nick_options = matched_nick_options
		self.search_widget = forms.TextInput(attrs = attrs)
		self.lookup_widget = SubmitButtonInput(button_text = 'Find name')
		super(NickWidget, self).__init__(attrs = attrs)
	
	def value_from_datadict(self, data, files, name):
		search_term = self.search_widget.value_from_datadict(data, files, name + '_search')
		if not search_term:
			return None
		
		explicit_lookup_requested = self.lookup_widget.value_from_datadict(data, files, name + '_lookup')
		
		nick_lookup = NickLookup(
			search_term = search_term,
			autoaccept = not explicit_lookup_requested,
			matched_nick_options = self.matched_nick_options)
		
		if not explicit_lookup_requested:
			nick_lookup.nick_selection = nick_lookup.matched_nick_field.widget.value_from_datadict(data, files, name + '_match')
		
		return nick_lookup
	
	def id_for_label(self, id_):
		if id_:
			id_ += '_search'
		return id_
	id_for_label = classmethod(id_for_label)
	
	def render(self, name, value, attrs=None):
		nick_lookup = NickLookup.from_value(value, matched_nick_options = self.matched_nick_options)
		
		search_html_output = [
			self.search_widget.render(name + '_search', nick_lookup.search_term, attrs = attrs),
			self.lookup_widget.render(name + '_lookup', None, attrs = attrs)
		]
		
		if nick_lookup.search_term:
			matched_nick_html = nick_lookup.matched_nick_field.widget.render(name + '_match', nick_lookup.nick_selection, attrs = attrs)
		else:
		    matched_nick_html = ''
		
		if self.matched_nick_options.get('sceners_only', False):
			root_classname = u'nick_field sceners_only'
		elif self.matched_nick_options.get('groups_only', False):
			root_classname = u'nick_field groups_only'
		else:
			root_classname = u'nick_field'
		
		output = [
			u'<div class="nick_search">' + u''.join(search_html_output) + u'</div>',
			u'<div class="nick_match_container">' + matched_nick_html + u'</div>'
		]
		return mark_safe(u'<div class="' + root_classname + u'">' + u''.join(output) + u'</div>')

class NickField(forms.Field):
	def __init__(self, sceners_only = False, groups_only = False, *args, **kwargs):
		self.matched_nick_options = {
			'sceners_only': sceners_only,
			'groups_only': groups_only,
		}
		self.widget = NickWidget(matched_nick_options = self.matched_nick_options)
		super(NickField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			return super(NickField, self).clean(value)
		else:
			nick_lookup = NickLookup.from_value(value, matched_nick_options = self.matched_nick_options)
			
			clean_nick_selection = nick_lookup.matched_nick_field.clean(nick_lookup.nick_selection)
			if clean_nick_selection and nick_lookup.autoaccept:
				return clean_nick_selection
			else:
				raise ValidationError("Please select the appropriate nick from the list.")

# test stuff
#
#class RaForm(forms.Form):
#	matched_nick = MatchedNickField('ra')
#
#raww_arse = Nick.objects.get(id = 7)
#
#lookup_ra_form = RaForm()
#edit_ra_form = RaForm(initial = {'matched_nick': raww_arse})
#posted_ra_form = RaForm({'matched_nick_id': '7', 'matched_nick_name': 'ra'})
#unresolved_ra_form = RaForm({'matched_nick_id': '', 'matched_nick_name': 'ra'})
#mischosen_ra_form = RaForm({'matched_nick_id': '1', 'matched_nick_name': 'ra'})
#
#class NewCreditForm(forms.Form):
#	nick = NickField()
#
#f = NewCreditForm(initial = {'nick': raww_arse})
