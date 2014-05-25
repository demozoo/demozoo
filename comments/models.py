from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class ProductionComment(models.Model):
	user = models.ForeignKey(User, related_name='production_comments')
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	commentable = generic.GenericForeignKey('content_type', 'object_id')

	body = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


class Commentable(models.Model):
	comments = generic.GenericRelation(ProductionComment)

	def get_comments(self):
		return self.comments.select_related('user').order_by('created_at')

	class Meta:
		abstract = True
