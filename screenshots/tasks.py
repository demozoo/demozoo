from celery.task import task
import os
import re
import uuid
import cStringIO
import zipfile

from six.moves import urllib

from productions.models import Screenshot, ProductionLink
from screenshots.models import PILConvertibleImage, USABLE_IMAGE_FILE_EXTENSIONS
from screenshots.processing import upload_to_s3, select_screenshot_file
from mirror.actions import fetch_link, find_screenshottable_graphics, find_zipped_screenshottable_graphics
from mirror.models import ArchiveMember
from django.conf import settings


upload_dir = os.path.join(settings.FILEROOT, 'media', 'screenshot_uploads')


def create_basename(screenshot_id):
        u = uuid.uuid4().hex
        return u[0:2] + '/' + u[2:4] + '/' + u[4:8] + '.' + str(screenshot_id) + '.'


def upload_original(img, screenshot, basename):
    orig, orig_size, orig_format = img.create_original()
    screenshot.original_url = upload_to_s3(orig, 'screens/o/' + basename + orig_format)
    screenshot.original_width, screenshot.original_height = orig_size


def upload_standard(img, screenshot, basename):
    standard, standard_size, standard_format = img.create_thumbnail((400, 300))
    screenshot.standard_url = upload_to_s3(standard, 'screens/s/' + basename + standard_format)
    screenshot.standard_width, screenshot.standard_height = standard_size


def upload_thumb(img, screenshot, basename):
    thumb, thumb_size, thumb_format = img.create_thumbnail((200, 150))
    screenshot.thumbnail_url = upload_to_s3(thumb, 'screens/t/' + basename + thumb_format)
    screenshot.thumbnail_width, screenshot.thumbnail_height = thumb_size


@task(ignore_result=True)
def create_screenshot_versions_from_local_file(screenshot_id, filename):
    try:
        screenshot = Screenshot.objects.get(id=screenshot_id)
        f = open(filename, 'rb')
        img = PILConvertibleImage(f, name_hint=filename)

        basename = create_basename(screenshot_id)
        upload_standard(img, screenshot, basename)
        upload_thumb(img, screenshot, basename)
        # leave original until last, because if it's already a websafe format it'll just return
        # the original file handle, and the storage backend might close the file after uploading
        # which screws with PIL's ability to create resized versions...
        upload_original(img, screenshot, basename)
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
        f = urllib.request.urlopen(screenshot.original_url, None, 10)
        # read into a cStringIO buffer so that PIL can seek on it (which isn't possible for urllib responses) -
        # see http://mail.python.org/pipermail/image-sig/2004-April/002729.html
        buf = cStringIO.StringIO(f.read())
        img = PILConvertibleImage(buf, screenshot.original_url.split('/')[-1])

        basename = create_basename(screenshot_id)
        upload_standard(img, screenshot, basename)
        upload_thumb(img, screenshot, basename)
        # leave original until last, because if it's already a websafe format it'll just return
        # the original file handle, and the storage backend might close the file after uploading
        # which screws with PIL's ability to create resized versions...
        upload_original(img, screenshot, basename)
        screenshot.save()

        f.close()

    except Screenshot.DoesNotExist:
        # guess it was deleted in the meantime, then.
        pass


@task(rate_limit='6/m', ignore_result=True)
def create_screenshot_from_production_link(production_link_id):
    try:
        prod_link = ProductionLink.objects.get(id=production_link_id)
    except ProductionLink.DoesNotExist:
        # guess it was deleted in the meantime, then.
        return

    if prod_link.production.screenshots.count():
        # don't create a screenshot if there's one already
        if prod_link.is_unresolved_for_screenshotting:
            prod_link.is_unresolved_for_screenshotting = False
            prod_link.save()
        return

    if prod_link.has_bad_image:
        return  # don't create a screenshot if a previous attempt has failed during image processing

    production_id = prod_link.production_id
    url = prod_link.download_url
    blob = fetch_link(prod_link)
    sha1 = blob.sha1

    if prod_link.is_zip_file():
        # select the archive member to extract a screenshot from, if we don't have
        # a candidate already
        archive_members = ArchiveMember.objects.filter(archive_sha1=sha1)
        if not prod_link.file_for_screenshot:
            file_for_screenshot = select_screenshot_file(archive_members)
            if file_for_screenshot:
                prod_link.file_for_screenshot = file_for_screenshot
                prod_link.is_unresolved_for_screenshotting = False
            else:
                prod_link.is_unresolved_for_screenshotting = True
            prod_link.save()

        image_extension = prod_link.file_for_screenshot.split('.')[-1].lower()
        if image_extension in USABLE_IMAGE_FILE_EXTENSIONS:
            z = None
            try:
                z = blob.as_zipfile()
                # we encode the filename as iso-8859-1 before retrieving it, because we
                # decoded it that way on insertion into the database to ensure that it had
                # a valid unicode string representation - see mirror/models.py
                member_buf = cStringIO.StringIO(
                    z.read(prod_link.file_for_screenshot.encode('iso-8859-1'))
                )
            except zipfile.BadZipfile:
                prod_link.has_bad_image = True
                prod_link.save()
                if z:  # pragma: no cover
                    z.close()
                return

            z.close()
            try:
                img = PILConvertibleImage(member_buf, name_hint=prod_link.file_for_screenshot)
            except IOError:
                prod_link.has_bad_image = True
                prod_link.save()
                return
        else:  # image is not a usable format
            return
    else:
        try:
            img = PILConvertibleImage(blob.as_io_buffer(), name_hint=url.split('/')[-1])
        except IOError:
            prod_link.has_bad_image = True
            prod_link.save()
            return

    screenshot = Screenshot(production_id=production_id)
    basename = sha1[0:2] + '/' + sha1[2:4] + '/' + sha1[4:8] + '.pl' + str(production_link_id) + '.'
    try:
        upload_standard(img, screenshot, basename)
        upload_thumb(img, screenshot, basename)
        # leave original until last, because if it's already a websafe format it'll just return
        # the original file handle, and the storage backend might close the file after uploading
        # which screws with PIL's ability to create resized versions...
        upload_original(img, screenshot, basename)
    except IOError:  # pragma: no cover
        prod_link.has_bad_image = True
        prod_link.save()
        return
    screenshot.save()


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


@task(ignore_result=True)
def fetch_remote_screenshots():
    for prod_link in find_screenshottable_graphics():
        create_screenshot_from_production_link.delay(prod_link.id)
    for prod_link in find_zipped_screenshottable_graphics():
        create_screenshot_from_production_link.delay(prod_link.id)
