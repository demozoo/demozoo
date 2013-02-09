import re
from django.db import models

from screenshots.models import IMAGE_FILE_EXTENSIONS

IGNORED_ARCHIVE_MEMBERS_RE = re.compile(r'(scene\.org\.txt|file_id\.diz)', re.I)


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

	def select_screenshot_file(self):
		interesting_files = []
		for member in self.archive_members.all():
			if not IGNORED_ARCHIVE_MEMBERS_RE.match(member.filename):
				interesting_files.append(member.filename)

		if len(interesting_files) == 1:
			filename = interesting_files[0]
			extension = filename.split('.')[-1]
			if filename != extension and extension.lower() in IMAGE_FILE_EXTENSIONS:
				return filename

		return None

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

	def __unicode__(self):
		return self.filename
