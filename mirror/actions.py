import urllib2
import os
import errno
import hashlib
import urlparse
import uuid
import re
import datetime

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings
from mirror.models import Download

user_agent = 'Demozoo/2.0 (gasman@raww.org; http://demozoo.org/)'
max_size = 1048576
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
	req = urllib2.Request(url, None, {'User-Agent': user_agent})
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


def upload_to_mirror(url, remote_filename, file_content):
	sha1 = hashlib.sha1(file_content).hexdigest()
	md5 = hashlib.md5(file_content).hexdigest()

	# look for an existing download with the same sha1
	download = None
	try:
		download = Download.objects.exclude(mirror_s3_key='').filter(sha1=sha1)[0]
	except IndexError:
		pass

	if download:
		# existing download was found; use the same mirror s3 key
		Download.objects.create(
			url=url,
			downloaded_at=datetime.datetime.now(),
			sha1=sha1,
			md5=md5,
			file_size=len(file_content),
			mirror_s3_key=download.mirror_s3_key
		)
	else:
		# no such download exists, so upload this one
		key_name = sha1[0:2] + '/' + sha1[2:4] + '/' + sha1[4:16] + '/' + clean_filename(remote_filename)
		bucket = open_bucket()
		k = Key(bucket)
		k.key = key_name
		k.set_contents_from_string(file_content)

		Download.objects.create(
			url=url,
			downloaded_at=datetime.datetime.now(),
			sha1=sha1,
			md5=md5,
			file_size=len(file_content),
			mirror_s3_key=key_name
		)


def fetch_url(url):
	# Fetch our mirrored copy of the given URL if available;
	# if not, mirror and return the original file

	try:
		# try to grab the most recent download of this URL which resulted in a mirror_s3_key
		download = Download.objects.filter(url=url).exclude(mirror_s3_key='').order_by('-downloaded_at')[0]
	except IndexError:
		# no mirrored copy exists - fetch and mirror the origin file
		try:
			remote_filename, file_content = fetch_origin_url(url)
		except (urllib2.URLError, FileTooBig) as ex:
			Download.objects.create(
				url=url,
				downloaded_at=datetime.datetime.now(),
				error_type=ex.__class__.__name__
			)
			raise
		upload_to_mirror(url, remote_filename, file_content)
		return remote_filename, file_content

	# existing download was found; fetch it
	bucket = open_bucket()
	k = Key(bucket)
	k.key = download.mirror_s3_key
	file_content = buffer(k.get_contents_as_string())
	remote_filename = download.mirror_s3_key.split('/')[-1]
	return remote_filename, file_content


def fetch_to_local(url):
	remote_filename, file_content = fetch_url(url)
	local_filename = uuid.uuid4().hex[:16] + '_' + clean_filename(remote_filename)
	local_path = os.path.join(upload_dir, local_filename)

	local_file = open(local_path, 'wb')
	local_file.write(file_content)
	local_file.close()
	return local_path
