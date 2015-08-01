from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from demoscene.models import Nick
from submit_button_field import SubmitButtonInput
from matched_nick_field import MatchedNickField
from demoscene.utils.nick_search import NickSelection, NickSearch


# An object which encapsulates the state of a NickWidget as derived from its posted data;
# this is what NickWidget returns from value_from_datadict
class NickLookup():
	def __init__(self,
		search_term=None, autoaccept=False,
		nick_selection=None,
		sceners_only=False, groups_only=False, prefer_members_of=None):

		self.search_term = search_term  # the search term being looked up
		self.autoaccept = autoaccept  # whether we should continue upon successfully resolving a nick,
			# as opposed to re-showing the form
		self.nick_selection = nick_selection

		if prefer_members_of:
			group_ids = [group.id for group in prefer_members_of]
		else:
			group_ids = []

		nick_search = NickSearch(search_term,
			sceners_only=sceners_only,
			groups_only=groups_only,
			group_ids=group_ids)
		self.matched_nick_field = MatchedNickField(nick_search, None)

	@staticmethod
	def from_value(value, sceners_only=False, groups_only=False, prefer_members_of=None):
		# value can be:
		# a Nick
		# None
		# an existing NickLookup
		if not value:
			return NickLookup(
				sceners_only=sceners_only, groups_only=groups_only,
				prefer_members_of=prefer_members_of)
		elif isinstance(value, NickLookup):
			return NickLookup(
				search_term=value.search_term,
				autoaccept=value.autoaccept,
				nick_selection=value.nick_selection,
				sceners_only=sceners_only, groups_only=groups_only,
				prefer_members_of=prefer_members_of)
		elif isinstance(value, Nick):
			return NickLookup(
				search_term=value.name,
				nick_selection=NickSelection(value.id, value.name),
				sceners_only=sceners_only, groups_only=groups_only,
				prefer_members_of=prefer_members_of)
		else:
			raise Exception("Don't know how to handle %s as a nick lookup" % repr(value))

	def __eq__(self, other):
		if not isinstance(other, NickLookup):
			return False
		return self.nick_selection == other.nick_selection

	def __ne__(self, other):
		return not self.__eq__(other)


class NickWidget(forms.Widget):
	def __init__(self, attrs=None, sceners_only=False, groups_only=False, prefer_members_of=None):
		self.sceners_only = sceners_only
		self.groups_only = groups_only
		self.prefer_members_of = prefer_members_of
		self.search_widget = forms.TextInput(attrs=attrs)
		self.lookup_widget = SubmitButtonInput(button_text='Find name')
		super(NickWidget, self).__init__(attrs=attrs)

	def value_from_datadict(self, data, files, name):
		search_term = self.search_widget.value_from_datadict(data, files, name + '_search')
		if not search_term:
			return None

		explicit_lookup_requested = self.lookup_widget.value_from_datadict(data, files, name + '_lookup')

		nick_lookup = NickLookup(
			search_term=search_term,
			autoaccept=not explicit_lookup_requested,
			sceners_only=self.sceners_only, groups_only=self.groups_only,
			prefer_members_of=self.prefer_members_of)

		if not explicit_lookup_requested:
			nick_lookup.nick_selection = nick_lookup.matched_nick_field.widget.value_from_datadict(data, files, name + '_match')

		return nick_lookup

	def id_for_label(self, id_):
		if id_:
			id_ += '_search'
		return id_
	id_for_label = classmethod(id_for_label)

	def render(self, name, value, attrs=None):
		nick_lookup = NickLookup.from_value(value,
			sceners_only=self.sceners_only, groups_only=self.groups_only,
			prefer_members_of=self.prefer_members_of)

		search_html_output = [
			self.search_widget.render(name + '_search', nick_lookup.search_term, attrs=attrs),
			'<input type="submit" style="display: none;">', # extra submit button so that whenever browsers insist on pretending a button was pressed when actually the user submitted the form with the enter key, they'll choose this button rather than the 'lookup' one
			self.lookup_widget.render(name + '_lookup', None, attrs=attrs)
		]

		if nick_lookup.search_term:
			matched_nick_html = nick_lookup.matched_nick_field.widget.render(name + '_match', nick_lookup.nick_selection, attrs=attrs)
		else:
			matched_nick_html = ''

		if self.sceners_only:
			root_classname = u'nick_field sceners_only'
		elif self.groups_only:
			root_classname = u'nick_field groups_only'
		else:
			root_classname = u'nick_field'

		if self.prefer_members_of:
			root_attrs = u' data-group_ids="%s"' % u','.join([str(group.id) for group in self.prefer_members_of])
		else:
			root_attrs = u''

		output = [
			u'<div class="nick_search">' + u''.join(search_html_output) + u'</div>',
			u'<div class="nick_match_container">' + matched_nick_html + u'</div>'
		]
		return mark_safe(u'<div class="' + root_classname + u'"' + root_attrs + u'>' + u''.join(output) + u'</div>')

	def _has_changed(self, initial, data):
		initial = NickLookup.from_value(initial)
		data = NickLookup.from_value(data)
		return data != initial


class NickField(forms.Field):
	def __init__(self, sceners_only=False, groups_only=False, prefer_members_of=None, *args, **kwargs):
		self.sceners_only = sceners_only
		self.groups_only = groups_only
		self.prefer_members_of = prefer_members_of
		self.widget = NickWidget(sceners_only=sceners_only, groups_only=groups_only, prefer_members_of=prefer_members_of)
		super(NickField, self).__init__(*args, **kwargs)

	def clean(self, value):
		if not value:
			return super(NickField, self).clean(value)
		else:
			nick_lookup = NickLookup.from_value(value, sceners_only=self.sceners_only, groups_only=self.groups_only, prefer_members_of=self.prefer_members_of)

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
