import re
import zipfile
import cStringIO
from django.db import models

from demoscene.models import ExternalLink
from demoscene.utils.groklinks import grok_production_link, PRODUCTION_LINK_TYPES
from screenshots.models import IMAGE_FILE_EXTENSIONS

# successively more aggressive rules for what files we should ignore in an archive
# when looking for screenshots - break out as soon as we have exactly one file remaining
IGNORED_ARCHIVE_MEMBER_RULES = [
	re.compile(r'(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz)$', re.I),
	re.compile(r'(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage\s*\d+\.\w+|.*steps?\s*\d+\.\w+|.*wip\s*\d+\.\w+)$', re.I),
	re.compile(r'(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage\s*\d+\.\w+|.*steps?\s*\d+\.\w+|.*wip\s*\d+\.\w+|.*vaihe\s*\d+\.\w+|.*phase\s*\d+\.\w+)$', re.I),
	re.compile(r'(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage\s*\d+\.\w+|.*steps?\s*\d+\.\w+|.*wip\s*\d+\.\w+|.*vaihe\s*\d+\.\w+|.*phase\s*\d+\.\w+|.*unsigned\.\w+|.*nosig\.\w+)$', re.I),
	re.compile(r'(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage.*|.*step.*|.*wip.*|.*vaihe.*|.*phase.*|.*unsigned.*|.*nosig.*|.*wire.*|.*malla.*|.*preview.*|.*work.*)$', re.I),
]


class Download(ExternalLink):
	downloaded_at = models.DateTimeField()
	sha1 = models.CharField(max_length=40, blank=True)
	md5 = models.CharField(max_length=32, blank=True)
	error_type = models.CharField(max_length=64, blank=True)
	file_size = models.IntegerField(null=True, blank=True)
	mirror_s3_key = models.CharField(max_length=255)

	link_types = PRODUCTION_LINK_TYPES

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
				file_size=info.file_size,
				archive_sha1=self.sha1)
			self.archive_members.add(member)

	def select_screenshot_file(self):
		for rule in IGNORED_ARCHIVE_MEMBER_RULES:
			interesting_files = []
			for member in self.archive_members.all():
				if member.file_size and not rule.match(member.filename):
					interesting_files.append(member)

			if len(interesting_files) == 1:
				break

		if len(interesting_files) == 1:
			if interesting_files[0].file_extension in IMAGE_FILE_EXTENSIONS:
				return interesting_files[0].filename

		return None

	def fetch_from_s3(self):
		from mirror.actions import open_bucket
		from boto.s3.key import Key

		bucket = open_bucket()
		k = Key(bucket)
		k.key = self.mirror_s3_key
		return buffer(k.get_contents_as_string())

	@staticmethod
	def last_mirrored_download_for_url(url):
		link = grok_production_link(url)
		link_class = link.__class__.__name__
		link_parameter = link.param

		try:
			# try to grab the most recent download of this URL which resulted in a mirror_s3_key
			return Download.objects.filter(
				link_class=link_class, parameter=link_parameter
			).exclude(mirror_s3_key='').order_by('-downloaded_at')[0]
		except IndexError:
			return None


class ArchiveMember(models.Model):
	download = models.ForeignKey(Download, related_name='archive_members')
	archive_sha1 = models.CharField(max_length=40, blank=True, db_index=True)
	filename = models.CharField(max_length=255)
	file_size = models.IntegerField()

	def __unicode__(self):
		return self.filename

	def fetch_from_zip(self):
		f = cStringIO.StringIO(self.download.fetch_from_s3())
		z = zipfile.ZipFile(f, 'r')
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
