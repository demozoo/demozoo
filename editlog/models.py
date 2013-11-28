import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class Edit(models.Model):
	action_type = models.CharField(max_length=100)
	user = models.ForeignKey('auth.User', related_name='edits')
	timestamp = models.DateTimeField()
	admin_only = models.BooleanField(default=False)
	detail = models.TextField(blank=True)

	def save(self, *args, **kwargs):
		if not self.timestamp:
			self.timestamp = datetime.datetime.now()
		super(Edit, self).save(*args, **kwargs)


class EditedItem(models.Model):
	edit = models.ForeignKey(Edit, related_name='edited_items')
	role = models.CharField(max_length=100)
	item_content_type = models.ForeignKey(ContentType, related_name='edited_items')
	item_id = models.PositiveIntegerField()
	item = generic.GenericForeignKey('item_content_type', 'item_id')
	name = models.CharField(max_length=255, blank=True)
