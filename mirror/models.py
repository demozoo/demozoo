import re
from django.db import models

from screenshots.models import IMAGE_FILE_EXTENSIONS

# successively more aggressive rules for what files we should ignore in an archive
# when looking for screenshots - break out as soon as we have exactly one file remaining
IGNORED_ARCHIVE_MEMBER_RULES = [
	re.compile(r'(__MACOSX.*|.*\.txt|.*\.nfo|.*\.diz)', re.I),
	re.compile(r'(__MACOSX.*|.*\.txt|.*\.nfo|.*\.diz|.*step\d+\.\w+)', re.I),
]


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
			# zip files do not contain information about the character encoding of filenames.
			# We therefore decode the filename as iso-8859-1 (an encoding which defines a character
			# for every byte value) to ensure that it is *some* valid sequence of unicode characters
			# that can be inserted into the database. When we need to access this zipfile entry
			# again, we will re-encode it as iso-8859-1 to get back the original byte sequence.
			member = ArchiveMember(
				filename=info.filename.decode('iso-8859-1'),
				file_size=info.file_size)
			self.archive_members.add(member)

	def select_screenshot_file(self):
		for rule in IGNORED_ARCHIVE_MEMBER_RULES:
			interesting_files = []
			for member in self.archive_members.all():
				if not rule.match(member.filename):
					interesting_files.append(member.filename)

			if len(interesting_files) == 1:
				break

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
