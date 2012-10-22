from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from demoscene.models import Nick, Releaser
from demoscene.utils.nick_search import NickSearch, NickSelection

# A variant of RadioFieldRenderer which accepts structs of:
# className, nameWithDifferentiator, nameWithAffiliations, countryCode, differentiator, alias, id
# and renders them as <li class="className" data-name="nameWithDifferentiator"> with a label containing
# a country flag, differentiator and alias as appropriate (in addition to nameWithAffiliations)
class NickChoicesRenderer(forms.widgets.RadioFieldRenderer):
	def render(self):
		from django.utils.encoding import force_unicode
		list_items = []
		for i, choice in enumerate(self.choices):
			
			if choice.get('countryCode'):
				flag = '<img src="/static/images/icons/flags/%s.png" data-countrycode="%s" alt="(%s)" /> ' % (
					conditional_escape(choice['countryCode']),
					conditional_escape(choice['countryCode']),
					conditional_escape(choice['countryCode'].upper())
				)
			else:
				flag = ''
			
			if choice.get('differentiator'):
				differentiator = ' <em class="differentiator">(%s)</em>' % conditional_escape(choice['differentiator'])
			else:
				differentiator = ''
			
			if choice.get('alias'):
				alias = ' <em class="alias">(%s)</em>' % conditional_escape(choice['alias'])
			else:
				alias = ''
			
			label = mark_safe(flag + choice['nameWithAffiliations'] + differentiator + alias)
			widget = forms.widgets.RadioInput(
				self.name, self.value, self.attrs.copy(), (choice['id'], label), i);
			
			list_items.append(
				u'<li class="%s" data-name="%s">%s</li>' % (choice['className'], conditional_escape(choice['nameWithDifferentiator']), force_unicode(widget))
			)
		return mark_safe(u'<ul>\n%s\n</ul>' % u'\n'.join(list_items))

class MatchedNickWidget(forms.Widget):
	def __init__(self, nick_search, attrs = None):
		
		self.nick_search = nick_search

		self.choices = self.nick_search.suggestions
		self.selection = self.nick_search.selection
		
		self.select_widget = forms.RadioSelect(renderer = NickChoicesRenderer,
			choices = self.choices, attrs = attrs)
		self.name_widget = forms.HiddenInput()
		
		super(MatchedNickWidget, self).__init__(attrs = attrs)
	
	@property
	def match_data(self):
		return self.nick_search.match_data
	
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
		selected_id = (value and value.id) or (self.selection and self.selection.id)
		output = [
			self.select_widget.render(
				name + '_id',
				selected_id,
				attrs = attrs),
			self.name_widget.render(name + '_name', self.nick_search.search_term, attrs = attrs)
		]
		return mark_safe(u'<div class="nick_match">' + u''.join(output) + u'</div>')

class MatchedNickField(forms.Field):
	def __init__(self, nick_search, *args, **kwargs):
		
		self.nick_search = nick_search
		
		self.widget = MatchedNickWidget(self.nick_search)
		
		super(MatchedNickField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			value = self.nick_search.selection
		elif isinstance(value, NickSelection):
			# check that it's a valid selection given the available choices
			if value.id == 'newscener' or value.id == 'newgroup':
				if value.name.lower() != self.nick_search.search_term.lower(): # invalid...
					value = self.nick_search.selection # ...so start a fresh match
			else:
				if int(value.id) not in [choice['id'] for choice in self.widget.choices]: # invalid...
					value = self.nick_search.selection # ...so start a fresh match
		elif isinstance(value, Nick):
			# convert to a NickSelection
			value = NickSelection(value.id, value.name)
		
		if isinstance(value, NickSelection) or value == None:
			return super(MatchedNickField, self).clean(value)
		else:
			raise Exception("Don't know how to clean %s" % repr(value))
