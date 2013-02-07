from celery.task import task
import os
import errno
import re
import uuid
import urllib2
import cStringIO

from demoscene.models import Screenshot
from screenshots.models import PILConvertibleImage
from screenshots.processing import upload_to_s3
from django.conf import settings


upload_dir = os.path.join(settings.FILEROOT, 'media', 'screenshot_uploads')
try:  # create upload_dir if not already present
	os.makedirs(upload_dir)
except OSError as exc:
	if exc.errno == errno.EEXIST and os.path.isdir(upload_dir):
		pass
	else:
		raise


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
		img = PILConvertibleImage(f)

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
@task(rate_limit='12/m', ignore_result=True)
def rebuild_screenshot(screenshot_id):
	try:
		screenshot = Screenshot.objects.get(id=screenshot_id)
		f = urllib2.urlopen(screenshot.original_url, None, 10)
		# read into a cStringIO buffer so that PIL can seek on it (which isn't possible for urllib2 responses) -
		# see http://mail.python.org/pipermail/image-sig/2004-April/002729.html
		buf = cStringIO.StringIO(f.read())
		img = PILConvertibleImage(buf)

		basename = create_basename(screenshot_id)
		upload_original(img, screenshot, basename)
		upload_standard(img, screenshot, basename)
		upload_thumb(img, screenshot, basename)
		screenshot.save()

		f.close()

	except Screenshot.DoesNotExist:
		# guess it was deleted in the meantime, then.
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
