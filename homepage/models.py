from django.db import models

from demoscene.utils.files import random_path


class Banner(models.Model):
	image = models.ImageField(
		upload_to=(lambda i, f: random_path('homepage_banners', f)),
		width_field='image_width', height_field='image_height')
	image_width = models.IntegerField(editable=False)
	image_height = models.IntegerField(editable=False)
	title = models.CharField(max_length=255)
	text = models.TextField(blank=True)
	url = models.CharField(max_length=255)

	show_for_anonymous_users = models.BooleanField(default=True)
	show_for_logged_in_users = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.title


class NewsStory(models.Model):
	title = models.CharField(max_length=255)
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.title

	class Meta:
		verbose_name_plural = 'News stories'
