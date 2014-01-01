from django.db import models
from django.contrib.auth.models import User

class NewsItem(models.Model):
	title = models.CharField(max_length=255, blank=True)
	body = models.TextField()
	created_at = models.DateTimeField()
	author = models.ForeignKey(User)

	def __unicode__(self):
		return self.title
