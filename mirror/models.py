from django.db import models


class Download(models.Model):
	url = models.CharField(max_length=255)
	downloaded_at = models.DateTimeField()
	sha1 = models.CharField(max_length=40, blank=True)
	md5 = models.CharField(max_length=32, blank=True)
	error_type = models.CharField(max_length=64, blank=True)
	file_size = models.IntegerField(null=True, blank=True)
	mirror_s3_key = models.CharField(max_length=255)
