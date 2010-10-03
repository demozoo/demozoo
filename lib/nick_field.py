from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from demoscene.models import Nick, NickVariant, Releaser
from submit_button_field import SubmitButtonInput

# A placeholder for a Nick object, used as the cleaned value of a MatchedNickField
# and the value MatchedNickWidget returns from value_from_datadict.
# We can't use a Nick because we may not want to save it to the database yet (because
# the form might be failing validation elsewhere), and using an unsaved Nick object
# isn't an option either because we need to create a Releaser as a side effect, and
# Django won't let us build multi-object structures of unsaved models.
class NickSelection():
	def __init__(self, id, name):
		self.id = id
		self.name = name
	
	def commit(self):
		if self.id == 'newscener':
			releaser = Releaser(name = self.name, is_group = False)
			releaser.save()
			self.id = releaser.primary_nick.id
			return releaser.primary_nick
		elif self.id == 'newgroup':
			releaser = Releaser(name = self.name, is_group = True)
			releaser.save()
			self.id = releaser.primary_nick.id
			return releaser.primary_nick
		else:
			return Nick.objects.get(id = self.id)
	
	def __str__(self):
		return "NickSelection: %s, %s" % (self.id, self.name)

# An object which encapsulates the state of a NickWidget as derived from its posted data;
# this is what NickWidget returns from value_from_datadict
class NickLookup():
	def __init__(self, search_term, autoaccept = False, favoured_selection = None):
		self.search_term = search_term # the search term being looked up
		self.autoaccept = autoaccept # whether we should continue upon successfully resolving a nick,
			# as opposed to re-showing the form
		self.favoured_selection = favoured_selection # a NickSelection that we should choose from the candidates if available

# A variant of RadioFieldRenderer which accepts 4-tuples as choices, using the third element
# as a classname for the <li> and fourth element as a data-name attribute
class RadioFieldWithClassnameRenderer(forms.widgets.RadioFieldRenderer):
	def render(self):
		from django.utils.encoding import force_unicode
		list_items = []
		for i, choice in enumerate(self.choices):
			widget = forms.widgets.RadioInput(self.name, self.value, self.attrs.copy(), choice, i);
			list_items.append(
				u'<li class="%s" data-name="%s">%s</li>' % (choice[2], choice[3], force_unicode(widget))
			)
		return mark_safe(u'<ul>\n%s\n</ul>' % u'\n'.join(list_items))

class MatchedNickWidget(forms.Widget):
	def __init__(self, search_term, attrs = None, sceners_only = False, groups_only = False):
		self.search_term = search_term
		
		choices = []
		self.nick_variants = NickVariant.autocompletion_search(
			search_term, exact = True, sceners_only = sceners_only, groups_only = groups_only)
		for nv in self.nick_variants:
			icon = 'group' if nv.nick.releaser.is_group else 'scener'
			if nv.nick.name == nv.name:
				choices.append((nv.nick_id, nv.nick.name_with_affiliations(), icon, nv.nick.name))
			else:
				label = "%s (%s)" % (nv.nick.name_with_affiliations(), nv.name)
				choices.append((nv.nick_id, label, icon, nv.nick.name))
		
		# see if there's a unique top choice in self.nick_variants;
		# if so, store that in self.top_choice for possible use later
		# if we render this widget with no initial value specified
		if self.nick_variants.count() == 0:
			self.top_choice = None
		elif self.nick_variants.count() == 1:
			self.top_choice = self.nick_variants[0]
		elif self.nick_variants[0].score > self.nick_variants[1].score:
			self.top_choice = self.nick_variants[0]
		else:
			self.top_choice = None
		
		if not groups_only:
			choices.append( ('newscener', "Add a new scener named '%s'" % search_term, "add_scener", search_term) )
		if not sceners_only:
			choices.append( ('newgroup', "Add a new group named '%s'" % search_term, "add_group", search_term) )
		
		self.select_widget = forms.RadioSelect(renderer = RadioFieldWithClassnameRenderer,
			choices = choices, attrs = attrs)
		self.name_widget = forms.HiddenInput()
		
		super(MatchedNickWidget, self).__init__(attrs = attrs)
	
	def value_from_datadict(self, data, files, name):
		nick_id = self.select_widget.value_from_datadict(data, files, name + '_id')
		nick_name = self.name_widget.value_from_datadict(data, files, name + '_name')
		if nick_id:
			return NickSelection(nick_id, nick_name)
		else:
			return None
	
	def id_for_label(self, id_):
		if id_:
			id_ += '_id'
		return id_
	id_for_label = classmethod(id_for_label)
	
	def render(self, name, value, attrs=None):
		selected_id = (value and value.id) or (self.top_choice and self.top_choice.nick_id)
		output = [
			self.select_widget.render(
				name + '_id',
				selected_id,
				attrs = attrs),
			self.name_widget.render(name + '_name', self.search_term, attrs = attrs)
		]
		return mark_safe(u''.join(output))

class MatchedNickField(forms.Field):
	def __init__(self, search_term, sceners_only = False, groups_only = False, *args, **kwargs):
		self.widget = MatchedNickWidget(
			search_term, sceners_only = sceners_only, groups_only = groups_only)
		
		self.search_term = search_term
		
		nick_variants = self.widget.nick_variants
		if nick_variants.count() == 0:
			self.best_match = None
		elif nick_variants.count() == 1:
			self.best_match = NickSelection(nick_variants[0].nick_id, nick_variants[0].name)
		elif nick_variants[0].score > nick_variants[1].score:
			self.best_match = NickSelection(nick_variants[0].nick_id, nick_variants[0].name)
		else:
			self.best_match = None
		
		super(MatchedNickField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			value = self.best_match
		elif isinstance(value, NickSelection):
			# check that it's a valid selection given the available choices
			if value.id == 'newscener' or value.id == 'newgroup':
				if value.name.lower() != self.search_term.lower(): # invalid...
					value = self.best_match # ...so start a fresh match
			else:
				if int(value.id) not in [nv.nick_id for nv in self.widget.nick_variants]: # invalid...
					value = self.best_match # ...so start a fresh match
		elif isinstance(value, Nick):
			# convert to a NickSelection
			value = NickSelection(nick.id, nick.name)
		
		if isinstance(value, NickSelection) or value == None:
			return super(MatchedNickField, self).clean(value)
		else:
			raise Exception("Don't know how to clean %s" % repr(value))

class NickWidget(forms.Widget):
	def __init__(self, attrs = None, sceners_only = False, groups_only = False):
		self.sceners_only = sceners_only
		self.groups_only = groups_only
		self.search_widget = forms.TextInput(attrs = attrs)
		self.lookup_widget = SubmitButtonInput(button_text = 'Find name')
		self.matched_nick_widget = None
		super(NickWidget, self).__init__(attrs = attrs)
	
	def value_from_datadict(self, data, files, name):
		search_term = self.search_widget.value_from_datadict(data, files, name + '_search')
		if not search_term:
			return None
		
		if self.lookup_widget.value_from_datadict(data, files, name + '_lookup'):
			return NickLookup(search_term, autoaccept = False)
		
		self.matched_nick_widget = MatchedNickWidget(search_term, None)
		nick_selection = self.matched_nick_widget.value_from_datadict(data, files, name + '_match')
		return NickLookup(search_term, autoaccept = True, favoured_selection = nick_selection)
	
	def id_for_label(self, id_):
		if id_:
			id_ += '_search'
		return id_
	id_for_label = classmethod(id_for_label)
	
	def render(self, name, value, attrs=None):
		if not value:
			value = NickLookup(None)
		elif isinstance(value, NickLookup):
			pass
		elif isinstance(value, Nick):
			value = NickLookup(value.name,
				favoured_selection = NickSelection(value.id, value.name))
		else:
			raise Exception("Don't know how to render %s" % repr(value))
		
		if value.search_term and not self.matched_nick_widget:
			self.matched_nick_widget = MatchedNickWidget(value.search_term)
		
		search_html_output = [
			self.search_widget.render(name + '_search', value.search_term, attrs = attrs),
			self.lookup_widget.render(name + '_lookup', None, attrs = attrs)
		]
		
		if value.search_term:
			matched_nick_html = self.matched_nick_widget.render(name + '_match', value.favoured_selection, attrs = attrs)
		else:
		    matched_nick_html = ''
		
		if self.sceners_only:
			root_classname = u'nick_field sceners_only'
		elif self.groups_only:
			root_classname = u'nick_field groups_only'
		else:
			root_classname = u'nick_field'
		
		output = [
			u'<div class="nick_search">' + u''.join(search_html_output) + u'</div>',
			u'<div class="nick_match">' + matched_nick_html + u'</div>'
		]
		return mark_safe(u'<div class="' + root_classname + u'">' + u''.join(output) + u'</div>')

class NickField(forms.Field):
	def __init__(self, sceners_only = False, groups_only = False, *args, **kwargs):
		self.widget = NickWidget(sceners_only = sceners_only, groups_only = groups_only)
		self.matched_nick_field_params = {
			'sceners_only': sceners_only,
			'groups_only': groups_only,
		}
		super(NickField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			return super(NickField, self).clean(value)
		elif isinstance(value, NickLookup):
			matched_nick_field = MatchedNickField(
				value.search_term, required = False, **self.matched_nick_field_params)
			clean_nick_selection = matched_nick_field.clean(value.favoured_selection)
			if clean_nick_selection and value.autoaccept:
				return clean_nick_selection
			else:
				self.widget.matched_nick_widget = matched_nick_field.widget
				raise ValidationError("Please select the appropriate nick from the list.")
		elif isinstance(value, Nick):
			matched_nick_field = MatchedNickField(value.name, required = False, **self.matched_nick_field_params)
			clean_nick_selection = matched_nick_field.clean(value)
			self.widget.matched_nick_widget = matched_nick_field.widget
			return clean_nick_selection

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
