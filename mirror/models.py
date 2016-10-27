import hashlib
import zipfile
import cStringIO

from django.db import models
from django.utils.functional import cached_property

from demoscene.models import ExternalLink
from demoscene.utils.groklinks import PRODUCTION_LINK_TYPES


class Download(ExternalLink):
	downloaded_at = models.DateTimeField()
	sha1 = models.CharField(max_length=40, blank=True)
	md5 = models.CharField(max_length=32, blank=True)
	error_type = models.CharField(max_length=64, blank=True)
	file_size = models.IntegerField(null=True, blank=True)
	mirror_s3_key = models.CharField(max_length=255)

	link_types = PRODUCTION_LINK_TYPES

	def get_archive_members(self):
		# get archive members by looking up on sha1
		return ArchiveMember.objects.filter(archive_sha1=self.sha1)

	def fetch_from_s3(self):
		from mirror.actions import open_bucket
		from boto.s3.key import Key

		bucket = open_bucket()
		k = Key(bucket)
		k.key = self.mirror_s3_key
		file_content = buffer(k.get_contents_as_string())
		filename = self.mirror_s3_key.split('/')[-1]
		return DownloadBlob(filename, file_content)


class ArchiveMember(models.Model):
	archive_sha1 = models.CharField(max_length=40, blank=True, db_index=True)
	filename = models.CharField(max_length=255)
	file_size = models.IntegerField()

	def __unicode__(self):
		return self.filename

	def fetch_from_zip(self):
		download = Download.objects.filter(sha1=self.archive_sha1).first()
		blob = download.fetch_from_s3()
		z = blob.as_zipfile()
		member_buf = cStringIO.StringIO(
			z.read(self.filename.encode('iso-8859-1'))
		)
		z.close()
		return member_buf

	@property
	def file_extension(self):
		extension = self.filename.split('.')[-1]
		if extension == self.filename:
			return None
		else:
			return extension.lower()

	def guess_mime_type(self):
		from screenshots.processing import MIME_TYPE_BY_EXTENSION
		return MIME_TYPE_BY_EXTENSION.get(self.file_extension, 'application/octet-stream')

	class Meta:
		ordering = ['filename']
		unique_together = [
			('archive_sha1', 'filename', 'file_size'),
		]


class DownloadBlob(object):
	def __init__(self, filename, file_content):
		self.filename = filename
		self.file_content = file_content

	@cached_property
	def md5(self):
		return hashlib.md5(self.file_content).hexdigest()

	@cached_property
	def sha1(self):
		return hashlib.sha1(self.file_content).hexdigest()

	@cached_property
	def file_size(self):
		return len(self.file_content)

	def as_io_buffer(self):
		return cStringIO.StringIO(self.file_content)

	def as_zipfile(self):
		return zipfile.ZipFile(self.as_io_buffer(), 'r')
