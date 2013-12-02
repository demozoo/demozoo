import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe


def releaser_for_edit_description(self):
	for item in self.edited_items.all():
		if item.role in ('scener', 'group', 'releaser'):
			return item

EDIT_DESCRIPTION_FORMATTERS = {
	'add_nick': (
		"Added %(nick)s as a nick for %(releaser)s",
		lambda self: {'nick': self.detail, 'releaser': releaser_for_edit_description(self)}
	),
	'create_group': (
		"Added group %(group)s",
		lambda self: {'group': self.get_item('group')}
	),
	'create_production': (
		 "Added production %(production)s",
		lambda self: {'production': self.get_item('production')}
	),
	'create_scener': (
		"Added scener %(scener)s",
		lambda self: {'scener': self.get_item('scener')}
	),
	'edit_party_notes': (
		"Edited notes for party %s",
		lambda self: {'party': self.get_item('party')}
	),
	'edit_production_core_details': (
		"Edited core details of %(production)s: %(detail)s",
		lambda self: {'production': self.get_item('production'), 'detail': self.detail}
	),
	'edit_production_notes': (
		"Edited notes for production %(production)s",
		lambda self: {'production': self.get_item('production')}
	),
	'edit_releaser_notes': (
		"Edited notes for %(releaser)s",
		lambda self: {'releaser': releaser_for_edit_description(self)}
	),
	'edit_scener_location': (
		"Set %(scener)s's location to %(location)s",
		lambda self: {'scener': self.get_item('scener'), 'location': self.detail}
	),
	'edit_scener_real_name': lambda self: (
		("Set %(scener)s's real name", lambda self: {'scener': self.get_item('scener')}) if self.detail == 'set_real_name'
		else ("Updated visibility of %(scener)s's real name", lambda self: {'scener': self.get_item('scener')})
	),
	'party_edit_external_links': (
		"%(detail)s on party %(party)s",
		lambda self: {'detail': self.detail, 'party': self.get_item('party')}
	),
	'production_edit_download_links': (
		"%(detail)s on production %(production)s",
		lambda self: {'detail': self.detail, 'production': self.get_item('production')}
	),
	'production_edit_external_links': (
		"%(detail)s on production %(production)s",
		lambda self: {'detail': self.detail, 'production': self.get_item('production')}
	),
	'releaser_edit_external_links': (
		"%(detail)s on %(releaser)s",
		lambda self: {'detail': self.detail, 'releaser': releaser_for_edit_description(self)}
	),
}


class Edit(models.Model):
	action_type = models.CharField(max_length=100)
	user = models.ForeignKey('auth.User', related_name='edits')
	timestamp = models.DateTimeField()
	admin_only = models.BooleanField(default=False)
	detail = models.TextField(blank=True)

	def get_item(self, role):
		for item in self.edited_items.all():
			if item.role == role:
				return item

	def save(self, *args, **kwargs):
		if not self.timestamp:
			self.timestamp = datetime.datetime.now()
		super(Edit, self).save(*args, **kwargs)

	def __unicode__(self):
		try:
			formatter = EDIT_DESCRIPTION_FORMATTERS[self.action_type]
		except KeyError:
			return self.action_type

		if callable(formatter):
			pattern, params_fn = formatter(self)
		else:
			pattern, params_fn = formatter

		params = params_fn(self)
		return pattern % params

	def html_description(self):
		try:
			formatter = EDIT_DESCRIPTION_FORMATTERS[self.action_type]
		except KeyError:
			return self.action_type

		if callable(formatter):
			pattern, params_fn = formatter(self)
		else:
			pattern, params_fn = formatter

		params = params_fn(self)
		for key, val in params.iteritems():
			try:
				params[key] = conditional_escape(val.html_name())
			except AttributeError:
				params[key] = conditional_escape(val)

		return mark_safe(pattern % params)


class EditedItem(models.Model):
	edit = models.ForeignKey(Edit, related_name='edited_items')
	role = models.CharField(max_length=100)
	item_content_type = models.ForeignKey(ContentType, related_name='edited_items')
	item_id = models.PositiveIntegerField()
	item = generic.GenericForeignKey('item_content_type', 'item_id')
	name = models.CharField(max_length=255, blank=True)

	def __unicode__(self):
		return self.name

	def html_name(self):
		url = None
		if self.role in ('production', 'soundtrack'):
			url = reverse('production', args=[self.item_id])
		elif self.role == 'party':
			url = reverse('party', args=[self.item_id])
		elif self.role in ('scener', 'member'):
			url = reverse('scener', args=[self.item_id])
		elif self.role in ('group', 'subgroup', 'supergroup'):
			url = reverse('group', args=[self.item_id])

		if url:
			return mark_safe('<a href="%s">%s</a>' % (escape(url), escape(self.name)))
		else:
			return mark_safe(escape(self.name))