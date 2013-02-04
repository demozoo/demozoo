from celery.task import task
import os

from demoscene.models import Screenshot
from screenshots.models import PILConvertibleImage
from screenshots.processing import upload_to_s3


@task(ignore_result=True)
def create_screenshot_versions_from_local_file(screenshot_id, filename):
	try:
		screenshot = Screenshot.objects.get(id=screenshot_id)
		f = open(filename, 'rb')
		img = PILConvertibleImage(f)

		orig, orig_size, orig_format = img.create_original()
		screenshot.original_url = upload_to_s3(orig, 'screens/o/', orig_format)
		screenshot.original_width, screenshot.original_height = orig_size

		standard, standard_size, standard_format = img.create_thumbnail((400, 300))
		screenshot.standard_url = upload_to_s3(standard, 'screens/s/', standard_format)
		screenshot.standard_width, screenshot.standard_height = standard_size

		thumb, thumb_size, thumb_format = img.create_thumbnail((200, 150))
		screenshot.thumbnail_url = upload_to_s3(thumb, 'screens/t/', thumb_format)
		screenshot.thumbnail_width, screenshot.thumbnail_height = thumb_size

		screenshot.save()

		f.close()
		os.remove(filename)

	except Screenshot.DoesNotExist:
		# guess it was deleted in the meantime, then.
		pass
