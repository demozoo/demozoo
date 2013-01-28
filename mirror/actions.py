import urllib2
import os
import errno
#import hashlib
import urlparse
import uuid
import re

from django.conf import settings

user_agent = 'Demozoo/2.0 (gasman@raww.org; http://demozoo.org/)'
max_size = 1048576

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


def fetch_url(url):
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
	cleaned_filename = re.sub(r'[^A-Za-z0-9\_\.\-]', '_', remote_filename)
	local_filename = uuid.uuid4().hex[:16] + '_' + cleaned_filename

	#sha1 = hashlib.sha1(file_content).hexdigest()
	local_file = open(os.path.join(upload_dir, local_filename), 'wb')
	local_file.write(file_content)
	local_file.close()
	return local_filename
