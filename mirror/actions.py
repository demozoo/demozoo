import urllib2
import os
import errno
import hashlib
import urlparse
import re
import datetime

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings
from mirror.models import Download
from screenshots.models import USABLE_IMAGE_FILE_EXTENSIONS
from screenshots.processing import select_screenshot_file
from productions.models import Production

max_size = 10485760
mirror_bucket_name = 'mirror.demozoo.org'

upload_dir = os.path.join(settings.FILEROOT, 'media', 'mirror')
try:  # create upload_dir if not already present
	os.makedirs(upload_dir)
except OSError as exc:
	if exc.errno == errno.EEXIST and os.path.isdir(upload_dir):
		pass
	else:
		raise


class FileTooBig(Exception):
	pass


def fetch_origin_url(url):
	# fetch file from the given URL (any protocol supported by urllib2),
	# throwing FileTooBig if it exceeds max_size
	req = urllib2.Request(url, None, {'User-Agent': settings.HTTP_USER_AGENT})
	f = urllib2.urlopen(req, None, 10)

	content_length = f.info().get('Content-Length')
	if content_length and int(content_length) > max_size:
		f.close()
		raise FileTooBig("File exceeded the size limit of %d bytes" % max_size)

	resolved_url = f.geturl()

	file_content = f.read(max_size + 1)
	f.close()
	if len(file_content) > max_size:
		raise FileTooBig("File exceeded the size limit of %d bytes" % max_size)

	remote_filename = urlparse.urlparse(resolved_url).path.split('/')[-1]

	return remote_filename, buffer(file_content)


def clean_filename(filename):
	return re.sub(r'[^A-Za-z0-9\_\.\-]', '_', filename)


def open_bucket():
	conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
	return conn.get_bucket(mirror_bucket_name)


def fetch_link(link):
	# Fetch our mirrored copy of the given link if available;
	# if not, mirror and return the original file

	url = link.download_url

	# find last mirrored download
	download = Download.objects.filter(
		link_class=link.link_class, parameter=link.parameter
	).exclude(mirror_s3_key='').order_by('-downloaded_at').first()

	if download:
		# existing download was found; fetch it
		return download, download.fetch_from_s3()
	else:
		# no mirrored copy exists - fetch and mirror the origin file
		try:
			remote_filename, file_content = fetch_origin_url(url)
		except (urllib2.URLError, FileTooBig) as ex:
			Download.objects.create(
				downloaded_at=datetime.datetime.now(),
				link_class=link.link_class,
				parameter=link.parameter,
				error_type=ex.__class__.__name__
			)
			raise

		sha1 = hashlib.sha1(file_content).hexdigest()
		md5 = hashlib.md5(file_content).hexdigest()
		download = Download(
			downloaded_at=datetime.datetime.now(),
			link_class=link.link_class,
			parameter=link.parameter,
			sha1=sha1,
			md5=md5,
			file_size=len(file_content),
		)

		# is there already a mirrored link with this sha1?
		existing_download = Download.objects.filter(sha1=sha1).first()
		if existing_download:
			download.mirror_s3_key = existing_download.mirror_s3_key
		else:
			key_name = sha1[0:2] + '/' + sha1[2:4] + '/' + sha1[4:16] + '/' + clean_filename(remote_filename)
			bucket = open_bucket()
			k = Key(bucket)
			k.key = key_name
			k.set_contents_from_string(file_content)
			download.mirror_s3_key = key_name

		download.save()

		return download, file_content


def find_screenshottable_graphics():
	# Graphic productions with downloads but no screenshots
	from django.db.models import Count
	prods = Production.objects.annotate(screenshot_count=Count('screenshots')).filter(
		supertype='graphics', screenshot_count=0, links__is_download_link=True).prefetch_related('links', 'platforms', 'types')

	prod_links = []
	for prod in prods:
		for link in prod.links.all():
			if link.is_download_link and link.download_file_extension() in USABLE_IMAGE_FILE_EXTENSIONS:
				prod_links.append(link)
				break  # ignore any remaining links for this prod

	return prod_links


def find_zipped_screenshottable_graphics():
	# Return a set of ProductionLink objects that link to archive files,
	# that we can plausibly expect to extract screenshots from, for productions that don't
	# have screenshots already.

	# prods of supertype=graphics that have download links but no screenshots
	from django.db.models import Count
	prods = Production.objects.annotate(screenshot_count=Count('screenshots')).filter(
		supertype='graphics', screenshot_count=0, links__is_download_link=True).prefetch_related('links', 'platforms', 'types')

	prod_links = []
	for prod in prods:
		for link in prod.links.all():

			if not (link.is_download_link and link.is_zip_file()):
				continue

			# skip ASCII and executable graphics
			if prod.types.filter(internal_name__in=['ascii', 'ascii-collection', 'ansi', 'exe-graphics', '4k-exe-graphics']):
				continue

			# skip prods for a specific platform other than DOS/Windows
			if prod.platforms.exclude(name__in=['MS-Dos', 'Windows']):
				continue

			file_for_screenshot = None
			# see if we've already got a best candidate archive member to take the image from
			if link.file_for_screenshot:
				file_for_screenshot = link.file_for_screenshot
			else:
				# failing that, see if we already have a directory listing for this download
				# and can derive a candidate from that
				archive_members = link.archive_members()
				if archive_members:
					file_for_screenshot = select_screenshot_file(archive_members)
					if file_for_screenshot:
						# we've found a candidate (which probably means we've improved select_screenshot_file
						# since it was last run on this archive) - might as well store it against the
						# ProductionLink, so it doesn't show up as something to be manually resolved
						link.file_for_screenshot = file_for_screenshot
						link.is_unresolved_for_screenshotting = False
						link.save()
					else:
						# we have a directory listing but no clear candidate, so give up on this link
						link.is_unresolved_for_screenshotting = True
						link.save()
						continue

			if file_for_screenshot:
				# we know in advance which file we'd like to extract from the archive -
				# better make sure it's a format we can actually handle, then.
				extension = link.file_for_screenshot.split('.')[-1].lower()
				if extension not in USABLE_IMAGE_FILE_EXTENSIONS:
					continue

			prod_links.append(link)
			break  # success, so ignore any remaining links for this prod

	return prod_links
