from __future__ import absolute_import, unicode_literals

import datetime
import errno
import os
import re
import urllib

import boto3
from django.conf import settings
from django.db.models import Count

from mirror.models import ArchiveMember, Download, DownloadBlob
from productions.models import Production
from screenshots.models import USABLE_IMAGE_FILE_EXTENSIONS
from screenshots.processing import select_screenshot_file


max_size = 10485760
mirror_bucket_name = 'mirror.demozoo.org'

upload_dir = os.path.join(settings.FILEROOT, 'media', 'mirror')
try:  # create upload_dir if not already present
    os.makedirs(upload_dir)
except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(upload_dir):
        pass
    else:  # pragma: no cover
        raise


class FileTooBig(Exception):
    pass


def fetch_origin_url(url):
    # fetch file from the given URL (any protocol supported by urllib),
    # throwing FileTooBig if it exceeds max_size
    req = urllib.request.Request(url, None, {'User-Agent': settings.HTTP_USER_AGENT})
    f = urllib.request.urlopen(req, None, 10)

    content_length = f.info().get('Content-Length')
    if content_length and int(content_length) > max_size:
        f.close()
        raise FileTooBig("File exceeded the size limit of %d bytes" % max_size)

    resolved_url = f.geturl()

    file_content = f.read(max_size + 1)
    f.close()
    if len(file_content) > max_size:
        raise FileTooBig("File exceeded the size limit of %d bytes" % max_size)

    remote_filename = urllib.parse.urlparse(resolved_url).path.split('/')[-1]

    return DownloadBlob(remote_filename, file_content)


def clean_filename(filename):
    return re.sub(r'[^A-Za-z0-9\_\.\-]', '_', filename)


def open_bucket():
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3 = session.resource('s3')
    return s3.Bucket(mirror_bucket_name)


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
        return download.fetch_from_s3()
    else:
        # no mirrored copy exists - fetch and mirror the origin file
        try:
            blob = fetch_origin_url(url)
        except (urllib.error.URLError, FileTooBig) as ex:
            Download.objects.create(
                downloaded_at=datetime.datetime.now(),
                link_class=link.link_class,
                parameter=link.parameter,
                error_type=ex.__class__.__name__
            )
            raise

        download = Download(
            downloaded_at=datetime.datetime.now(),
            link_class=link.link_class,
            parameter=link.parameter,
            sha1=blob.sha1,
            md5=blob.md5,
            file_size=blob.file_size,
        )

        # is there already a mirrored link with this sha1?
        existing_download = Download.objects.filter(sha1=blob.sha1).first()
        if existing_download:
            download.mirror_s3_key = existing_download.mirror_s3_key
        else:
            key_name = blob.sha1[0:2] + '/' + blob.sha1[2:4] + '/' + blob.sha1[4:16] + '/' + clean_filename(blob.filename)
            bucket = open_bucket()
            obj = bucket.put_object(Key=key_name, Body=blob.file_content)
            download.mirror_s3_key = key_name

        download.save()

        if link.is_zip_file():
            # catalogue the zipfile contents if we don't have them already
            if not ArchiveMember.objects.filter(archive_sha1=blob.sha1).exists():
                z = blob.as_zipfile()
                for info in z.infolist():
                    # The Incredible Disaster of Platform Specific Implementations of Zip:
                    # https://gist.github.com/jnalley/cec21bca2d865758bc5e23654df28bd5
                    #
                    # Historically, zip files did not specify what character encoding the filename is using;
                    # there is supposedly a flag to indicate 'yo this is utf-8' but it's unclear how widely
                    # used/recognised it is, and you can bet that scene.org has some weird shit on it.
                    # So, we consider the filename to be an arbitrary byte string.
                    #
                    # Since the database wants to store unicode strings, we decode the byte string as
                    # iso-8859-1 to obtain one, and encode it as iso-8859-1 again on the way out of the
                    # database. iso-8859-1 is chosen because it gives a well-defined result for any
                    # arbitrary byte string, and doesn't unnecessarily mangle pure ASCII filenames.
                    #
                    # So, how do we get a byte string from the result of ZipFile.infolist?
                    # Python 2 gives us a unicode string if the mythical utf-8 flag is set,
                    # and a byte string otherwise. Our old python-2-only code called
                    # filename.decode('iso-8859-1'), which would have failed on a unicode string containing
                    # non-ascii characters, so we can assume that anything that made it as far as the
                    # database originated either as pure ascii or a bytestring. Either way, calling
                    # database_value.encode('iso-8859-1') would give a bytestring that python 2's zipfile
                    # library can accept (i.e. it compares equal to the filename it originally gave us).
                    #
                    # Python 3 ALWAYS gives us a unicode string: decoded as utf-8 if the mythical flag is
                    # set, or decoded as cp437 if not. We don't need to know which of these outcomes
                    # happened; we just need to ensure that
                    # 1) the transformation from unicode string to byte string is reversible, and
                    # 2) the byte string representation matches the one that python 2 would have given us
                    # for the same filename.
                    #
                    # The latter condition is satisfied by filename.encode('cp437'), which makes the
                    # reverse tranformation bytestring.decode('cp437'). Therefore our final algorithm is:
                    #
                    # zipfile to database:
                    # if filename is a unicode string (i.e. we are on py3 or the mythical flag is set):
                    #     filename = filename.encode('cp437')  # filename is now a bytestring
                    # return filename.decode('iso-8859-1')
                    #
                    # database to zipfile:
                    # bytestring = database_value.encode('iso-8859-1')
                    # if we are on py2:
                    #     return bytestring
                    # else:
                    #     return bytestring.decode('cp437')
                    #

                    filename = info.filename
                    if isinstance(filename, str):  # pragma: no cover
                        filename = filename.encode('cp437')
                    filename = filename.decode('iso-8859-1')

                    ArchiveMember.objects.get_or_create(
                        filename=filename,
                        file_size=info.file_size,
                        archive_sha1=blob.sha1)

        return blob


def unpack_db_zip_filename(filename):
    bytestring = filename.encode('iso-8859-1')
    return bytestring.decode('cp437')


def find_screenshottable_graphics():
    # Graphic productions with downloads but no screenshots
    from django.db.models import Count
    prods = Production.objects.annotate(screenshot_count=Count('screenshots')).filter(
        supertype='graphics', screenshot_count=0, links__is_download_link=True).prefetch_related('links')

    prod_links = []
    for prod in prods:
        for link in prod.links.all():
            if (
                link.is_download_link and not link.has_bad_image
                and link.download_file_extension() in USABLE_IMAGE_FILE_EXTENSIONS and link.is_believed_downloadable()
            ):
                prod_links.append(link)
                break  # ignore any remaining links for this prod

    return prod_links


def find_zipped_screenshottable_graphics():
    # Return a set of ProductionLink objects that link to archive files,
    # that we can plausibly expect to extract screenshots from, for productions that don't
    # have screenshots already.

    # prods of supertype=graphics that have download links but no screenshots
    prods = Production.objects.annotate(screenshot_count=Count('screenshots')).filter(
        supertype='graphics', screenshot_count=0, links__is_download_link=True).prefetch_related('links', 'types')

    prod_links = []
    for prod in prods:

        # skip ASCII/ANSI prods
        if prod.types.filter(internal_name__in=['ascii', 'ascii-collection', 'ansi']):
            continue

        for link in prod.links.all():

            if not (link.is_download_link and link.is_zip_file()):
                continue

            if link.has_bad_image or not link.is_believed_downloadable():
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
