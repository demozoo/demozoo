from django.db import models
from django.contrib.auth.models import User

from demoscene.models import Production

class ProductionComment(models.Model):
	user = models.ForeignKey(User, related_name='production_comments')
	production = models.ForeignKey(Production, related_name='comments')

	body = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
