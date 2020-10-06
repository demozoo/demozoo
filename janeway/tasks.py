from __future__ import absolute_import, unicode_literals

from celery.task import task

from demoscene.models import Releaser, ReleaserExternalLink
from janeway.matching import automatch_productions
from mirror.actions import fetch_origin_url
from productions.models import Screenshot
from screenshots.models import PILConvertibleImage
from screenshots.tasks import upload_original, upload_standard, upload_thumb


@task(ignore_result=True)
def automatch_all_authors():
    for releaser_id in ReleaserExternalLink.objects.filter(link_class='KestraBitworldAuthor').distinct().values_list('releaser_id', flat=True):
        automatch_author.delay(releaser_id)


@task(rate_limit='6/m', ignore_result=True)
def automatch_author(releaser_id):
    automatch_productions(Releaser.objects.get(id=releaser_id))


@task(rate_limit='6/m', ignore_result=True)
def import_screenshot(production_id, janeway_id, url, suffix):
    blob = fetch_origin_url(url)
    sha1 = blob.sha1
    img = PILConvertibleImage(blob.as_io_buffer(), name_hint=blob.filename)
    basename = sha1[0:2] + '/' + sha1[2:4] + '/' + sha1[4:8] + '.jw' + str(janeway_id) + suffix + '.'

    screenshot = Screenshot(
        production_id=production_id,
        data_source='janeway', janeway_id=janeway_id, janeway_suffix=suffix
    )
    upload_standard(img, screenshot, basename)
    upload_thumb(img, screenshot, basename)
    # leave upload_original until last to prevent things screwing up if the storage
    # closes the original file handle
    upload_original(img, screenshot, basename)
    screenshot.save()
