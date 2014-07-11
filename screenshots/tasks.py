from celery.task import task
import os
import re
import uuid
import urllib2
import cStringIO
import zipfile

from productions.models import Screenshot, ProductionLink
from screenshots.models import PILConvertibleImage, USABLE_IMAGE_FILE_EXTENSIONS
from screenshots.processing import upload_to_s3
from mirror.actions import fetch_url, FileTooBig
from django.conf import settings


upload_dir = os.path.join(settings.FILEROOT, 'media', 'screenshot_uploads')


def create_basename(screenshot_id):
		u = uuid.uuid4().hex
		return u[0:2] + '/' + u[2:4] + '/' + u[4:8] + '.' + str(screenshot_id) + '.'


def upload_original(img, screenshot, basename, reduced_redundancy=False):
	orig, orig_size, orig_format = img.create_original()
	screenshot.original_url = upload_to_s3(orig, 'screens/o/' + basename + orig_format, orig_format, reduced_redundancy=reduced_redundancy)
	screenshot.original_width, screenshot.original_height = orig_size


def upload_standard(img, screenshot, basename):  # always reduced redundancy
	standard, standard_size, standard_format = img.create_thumbnail((400, 300))
	screenshot.standard_url = upload_to_s3(standard, 'screens/s/' + basename + standard_format, standard_format, reduced_redundancy=True)
	screenshot.standard_width, screenshot.standard_height = standard_size


def upload_thumb(img, screenshot, basename):  # always reduced redundancy
	thumb, thumb_size, thumb_format = img.create_thumbnail((200, 150))
	screenshot.thumbnail_url = upload_to_s3(thumb, 'screens/t/' + basename + thumb_format, thumb_format, reduced_redundancy=True)
	screenshot.thumbnail_width, screenshot.thumbnail_height = thumb_size


@task(ignore_result=True)
def create_screenshot_versions_from_local_file(screenshot_id, filename):
	try:
		screenshot = Screenshot.objects.get(id=screenshot_id)
		f = open(filename, 'rb')
		img = PILConvertibleImage(f, name_hint=filename)

		basename = create_basename(screenshot_id)
		upload_original(img, screenshot, basename)
		upload_standard(img, screenshot, basename)
		upload_thumb(img, screenshot, basename)
		screenshot.save()

		f.close()

	except Screenshot.DoesNotExist:
		# guess it was deleted in the meantime, then.
		pass

	os.remove(filename)


# token rate limit so that new uploads from local files get priority
@task(rate_limit='1/s', ignore_result=True)
def rebuild_screenshot(screenshot_id):
	try:
		screenshot = Screenshot.objects.get(id=screenshot_id)
		f = urllib2.urlopen(screenshot.original_url, None, 10)
		# read into a cStringIO buffer so that PIL can seek on it (which isn't possible for urllib2 responses) -
		# see http://mail.python.org/pipermail/image-sig/2004-April/002729.html
		buf = cStringIO.StringIO(f.read())
		img = PILConvertibleImage(buf, screenshot.original_url.split('/')[-1])

		basename = create_basename(screenshot_id)
		upload_original(img, screenshot, basename)
		upload_standard(img, screenshot, basename)
		upload_thumb(img, screenshot, basename)
		screenshot.save()

		f.close()

	except Screenshot.DoesNotExist:
		# guess it was deleted in the meantime, then.
		pass


@task(rate_limit='6/m', ignore_result=True)
def create_screenshot_from_production_link(production_link_id):
	try:
		prod_link = ProductionLink.objects.get(id=production_link_id)
		if prod_link.production.screenshots.count():
			return  # don't create a screenshot if there's one already

		production_id = prod_link.production_id
		url = prod_link.download_url
		download, file_content = fetch_url(url)
		buf = cStringIO.StringIO(file_content)

		if prod_link.is_zip_file():
			z = zipfile.ZipFile(buf, 'r')
			# catalogue the zipfile contents if we don't have them already
			if not download.archive_members.all():
				download.log_zip_contents(z)
			# select the archive member to extract a screenshot from, if we don't have
			# a candidate already
			if not prod_link.file_for_screenshot:
				file_for_screenshot = download.select_screenshot_file()
				if file_for_screenshot:
					prod_link.file_for_screenshot = file_for_screenshot
					prod_link.is_unresolved_for_screenshotting = False
				else:
					prod_link.is_unresolved_for_screenshotting = True
				prod_link.save()

			image_extension = prod_link.file_for_screenshot.split('.')[-1].lower()
			if image_extension in USABLE_IMAGE_FILE_EXTENSIONS:
				# we encode the filename as iso-8859-1 before retrieving it, because we
				# decoded it that way on insertion into the database to ensure that it had
				# a valid unicode string representation - see mirror/models.py
				member_buf = cStringIO.StringIO(
					z.read(prod_link.file_for_screenshot.encode('iso-8859-1'))
				)
				z.close()
				img = PILConvertibleImage(member_buf, name_hint=prod_link.file_for_screenshot)
			else:  # image is not a usable format
				z.close()
				return
		else:
			img = PILConvertibleImage(buf, name_hint=url.split('/')[-1])

		screenshot = Screenshot(production_id=production_id, source_download_id=download.id)
		u = download.sha1
		basename = u[0:2] + '/' + u[2:4] + '/' + u[4:8] + '.pl' + str(production_link_id) + '.'
		upload_original(img, screenshot, basename, reduced_redundancy=True)
		upload_standard(img, screenshot, basename)
		upload_thumb(img, screenshot, basename)
		screenshot.save()

	except ProductionLink.DoesNotExist:
		# guess it was deleted in the meantime, then.
		pass


# DEPRECATED
@task(rate_limit='6/m', ignore_result=True)
def create_screenshot_from_remote_file(url, production_id):
	try:
		download, file_content = fetch_url(url)
		screenshot = Screenshot(production_id=production_id, source_download_id=download.id)

		buf = cStringIO.StringIO(file_content)
		img = PILConvertibleImage(buf, name_hint=url.split('/')[-1])

		u = download.sha1
		basename = u[0:2] + '/' + u[2:4] + '/' + u[4:8] + '.p' + str(production_id) + '.'
		upload_original(img, screenshot, basename, reduced_redundancy=True)
		upload_standard(img, screenshot, basename)
		upload_thumb(img, screenshot, basename)
		screenshot.save()

	except (urllib2.URLError, FileTooBig):
		# oh well.
		pass


def capture_upload_for_processing(uploaded_file, screenshot_id):
	"""
		Save an UploadedFile to our holding area on the local filesystem and schedule
		for screenshot processing
	"""
	clean_filename = re.sub(r'[^A-Za-z0-9\_\.\-]', '_', uploaded_file.name)
	local_filename = uuid.uuid4().hex[0:16] + clean_filename
	path = os.path.join(upload_dir, local_filename)
	destination = open(path, 'wb')
	for chunk in uploaded_file.chunks():
		destination.write(chunk)
	destination.close()
	create_screenshot_versions_from_local_file.delay(screenshot_id, path)
