from django.db import models


class Download(models.Model):
	url = models.CharField(max_length=255)
	downloaded_at = models.DateTimeField()
	sha1 = models.CharField(max_length=40, blank=True)
	md5 = models.CharField(max_length=32, blank=True)
	error_type = models.CharField(max_length=64, blank=True)
	file_size = models.IntegerField(null=True, blank=True)
	mirror_s3_key = models.CharField(max_length=255)

	@staticmethod
	def last_mirrored_download_for_url(url):
		try:
			# try to grab the most recent download of this URL which resulted in a mirror_s3_key
			return Download.objects.filter(url=url).exclude(mirror_s3_key='').order_by('-downloaded_at')[0]
		except IndexError:
			return None
