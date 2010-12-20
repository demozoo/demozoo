from django import template

# {% spawningformset for form in formset %}
# ...
# {% endspawningformset %}

register = template.Library()

import re

@register.tag
def spawningformset(parser, token):
	try:
		# Splitting by None == splitting by spaces.
		tag_name, arg = token.contents.split(None, 1)
	except ValueError:
		raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
	m = re.search(r'(sortable )?for (\w+) in (\w+)', arg)
	if not m:
		raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
	sortable, form_var_name, formset_name = m.groups()
	
	nodelist = parser.parse(('endspawningformset',))
	parser.delete_first_token()
	return SpawningFormsetNode(sortable, form_var_name, formset_name, nodelist)

class SpawningFormsetNode(template.Node):
	def __init__(self, sortable, form_var_name, formset_name, nodelist):
		self.sortable = sortable
		self.form_var_name = form_var_name
		self.formset_var = template.Variable(formset_name)
		self.nodelist = nodelist
	
	def render(self, context):
		try:
			formset = self.formset_var.resolve(context)
		except template.VariableDoesNotExist:
			return ''
		
		if self.sortable:
			class_attr = ' class="sortable_formset"'
		else:
			class_attr = ''
		output = [
			u'<div class="field_input spawning_formset">',
			str(formset.management_form),
			u'<ul%s>' % class_attr,
		]
		
		for form in formset.forms:
			context[self.form_var_name] = form
			if form.is_bound:
				li_class = 'bound'
			else:
				li_class = 'unbound'
			if self.sortable:
				li_class += ' sortable_item'
			
			if 'DELETE' in form.fields:
				delete_field = u'<span class="delete">%s %s</span>' % (form['DELETE'], form['DELETE'].label_tag())
			else:
				delete_field = ''
			output += [
				u'<li class="%s">' % li_class,
				u'<div class="formset_item">',
				self.nodelist.render(context),
				u'</div>',
				delete_field,
				u'</li>'
			]
		
		form = formset.empty_form
		context[self.form_var_name] = form
		if 'DELETE' in form.fields:
			delete_field = u'<span class="delete">%s %s</span>' % (form['DELETE'], form['DELETE'].label_tag())
		else:
			delete_field = ''
		li_class = 'placeholder_form'
		if self.sortable:
			li_class += ' sortable_item'
		output += [
			u'<li class="%s">' % li_class,
			u'<div class="formset_item">',
			self.nodelist.render(context),
			u'</div>',
			delete_field,
			u'</li>',
			u'</ul>',
			u'</div>',
		]
		
		return u''.join(output)
		