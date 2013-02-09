from django.db import models


class Download(models.Model):
	url = models.CharField(max_length=255)
	downloaded_at = models.DateTimeField()
	sha1 = models.CharField(max_length=40, blank=True)
	md5 = models.CharField(max_length=32, blank=True)
	error_type = models.CharField(max_length=64, blank=True)
	file_size = models.IntegerField(null=True, blank=True)
	mirror_s3_key = models.CharField(max_length=255)

	@property
	def filename(self):
		return self.mirror_s3_key.split('/')[-1]

	def log_zip_contents(self, zip_file):
		for info in zip_file.infolist():
			member = ArchiveMember(filename=info.filename, file_size=info.file_size)
			self.archive_members.add(member)

	@staticmethod
	def last_mirrored_download_for_url(url):
		try:
			# try to grab the most recent download of this URL which resulted in a mirror_s3_key
			return Download.objects.filter(url=url).exclude(mirror_s3_key='').order_by('-downloaded_at')[0]
		except IndexError:
			return None


class ArchiveMember(models.Model):
	download = models.ForeignKey(Download, related_name='archive_members')
	filename = models.CharField(max_length=255)
	file_size = models.IntegerField()
