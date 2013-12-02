import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


def releaser_for_edit_description(self):
	for item in self.edited_items.all():
		if item.role in ('scener', 'group', 'releaser'):
			return "%s %s" % (item.role, item.name)

EDIT_DESCRIPTION_FORMATTERS = {
	'add_nick': lambda self: "Added %s as a nick for %s" % (self.detail, releaser_for_edit_description(self)),
	'create_group': lambda self: "Added group %s" % (self.get_item('group').name),
	'create_production': lambda self: "Added production %s" % (self.get_item('production').name),
	'create_scener': lambda self: "Added scener %s" % (self.get_item('scener').name),
	'edit_party_notes': lambda self: "Edited notes for party %s" % (self.get_item('party').name),
	'edit_production_core_details': lambda self: "Edited core details of %s: %s" % (self.get_item('production').name, self.detail),
	'edit_production_notes': lambda self: "Edited notes for production %s" % (self.get_item('production').name),
	'edit_releaser_notes': lambda self: "Edited notes for %s" % releaser_for_edit_description(self),
	'edit_scener_location': lambda self: "Set %s's location to %s" % (self.get_item('scener').name, self.detail),
	'edit_scener_real_name': lambda self: ("Set %s's real name" % (self.get_item('scener').name)) if self.detail == 'set_real_name' else ("Updated visibility of %s's real name" % (self.get_item('scener').name)),
	'party_edit_external_links': lambda self: "%s on party %s" % (self.detail, self.get_item('party').name),
	'production_edit_download_links': lambda self: "%s on production %s" % (self.detail, self.get_item('production').name),
	'production_edit_external_links': lambda self: "%s on production %s" % (self.detail, self.get_item('production').name),
	'releaser_edit_external_links': lambda self: "%s on %s" % (self.detail, releaser_for_edit_description(self)),
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
		formatter = EDIT_DESCRIPTION_FORMATTERS.get(self.action_type)
		if formatter:
			return formatter(self)
		else:
			return self.action_type


class EditedItem(models.Model):
	edit = models.ForeignKey(Edit, related_name='edited_items')
	role = models.CharField(max_length=100)
	item_content_type = models.ForeignKey(ContentType, related_name='edited_items')
	item_id = models.PositiveIntegerField()
	item = generic.GenericForeignKey('item_content_type', 'item_id')
	name = models.CharField(max_length=255, blank=True)
