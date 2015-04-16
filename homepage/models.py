from django.db import models

from demoscene.utils.files import random_path


class Banner(models.Model):
	image = models.ImageField(
		upload_to=(lambda i, f: random_path('homepage_banners', f)),
		width_field='image_width', height_field='image_height')
	image_width = models.IntegerField(editable=False)
	image_height = models.IntegerField(editable=False)
	banner_image = models.ForeignKey('BannerImage', null=True, blank=True, related_name='+',
		on_delete=models.SET_NULL,  # don't want deletion to cascade to the banner if image is deleted
	)
	title = models.CharField(max_length=255)
	text = models.TextField(blank=True)
	url = models.CharField(max_length=255)

	show_for_anonymous_users = models.BooleanField(default=True)
	show_for_logged_in_users = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.title


class BannerImage(models.Model):
	image = models.ImageField(
		upload_to=(lambda i, f: random_path('homepage_banners', f)),
		width_field='image_width', height_field='image_height')
	image_width = models.IntegerField(editable=False)
	image_height = models.IntegerField(editable=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# method for displaying image in admin listings
	def image_tag(self):
		return '<img src="%s" width="400" alt="" />' % self.image.url
	image_tag.allow_tags = True

	def __unicode__(self):
		return self.image.name


class NewsStory(models.Model):
	title = models.CharField(max_length=255)
	text = models.TextField()
	image = models.ForeignKey('NewsImage', null=True, blank=True, related_name='+',
		on_delete=models.SET_NULL,  # don't want deletion to cascade to the news story if image is deleted
	)
	is_public = models.BooleanField(blank=True, default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.title

	class Meta:
		verbose_name_plural = 'News stories'


class NewsImage(models.Model):
	image = models.ImageField(
		upload_to=(lambda i, f: random_path('news_images', f)),
		width_field='image_width', height_field='image_height',
		help_text='Recommended size: 100x100')
	image_width = models.IntegerField(editable=False)
	image_height = models.IntegerField(editable=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# method for displaying image in admin listings
	def image_tag(self):
		return '<img src="%s" width="100" alt="" />' % self.image.url
	image_tag.allow_tags = True

	def __unicode__(self):
		return self.image.name
