from celery.task import task
from sceneorg.models import Directory, File
from sceneorg.scraper import scrape_dir
from sceneorg.dirparser import parse_all_dirs
from demoscene.tasks import find_sceneorg_results_files
import datetime
import logging
import time
import urllib2
import json

from django.conf import settings


# Get an instance of a logger
logger = logging.getLogger(__name__)


@task(time_limit=3600, ignore_result=True)
def fetch_new_sceneorg_files(days=1):
	url = "https://files.scene.org/api/adhoc/latest-files/?days=%d" % days

	new_file_count = 0

	while True:
		req = urllib2.Request(url, None, {'User-Agent': settings.HTTP_USER_AGENT})
		page = urllib2.urlopen(req)
		response = json.loads(page.read())
		page.close()

		if not response.get('success'):
			logger.warning("scene.org API request returned non-success! %r" % response)
			break

		logger.info("API request to %s succeeded - %d files returned" % (url, len(response['files'])))

		for item in response['files']:
			path_components = item['fullPath'].split('/')[1:]
			dirs = path_components[:-1]

			path = '/'
			current_dir = Directory.objects.get_or_create(
				path='/', defaults={'last_seen_at': datetime.datetime.now()})

			for d in dirs:
				last_dir = current_dir
				path += d + '/'

				try:
					current_dir = Directory.objects.get(path=path)
					current_dir.last_seen_at = datetime.datetime.now()
					current_dir.is_deleted = False
					current_dir.save()
				except Directory.DoesNotExist:
					current_dir = Directory.objects.create(path=path, last_seen_at=datetime.datetime.now(), parent=last_dir)

			path += path_components[-1]

			try:
				f = File.objects.get(path=path)
				f.last_seen_at = datetime.datetime.now()
				f.is_deleted = False
				f.size = item['size']
				f.save()
			except File.DoesNotExist:
				logger.info("New file found: %s" % path)
				File.objects.create(
					path=path, last_seen_at=datetime.datetime.now(), directory=current_dir,
					size=item['size'])
				new_file_count += 1

		url = response.get('nextPageURL')
		if url:
			time.sleep(1)
		else:
			break

	if new_file_count > 0:
		find_sceneorg_results_files()


# files.scene.org frontend scraper - no longer used
@task(rate_limit='6/m', ignore_result=True)
def fetch_sceneorg_dir(path, async=True):
	try:
		dir = Directory.objects.get(path=path)
	except Directory.DoesNotExist:
		dir = Directory.objects.create(path=path, last_seen_at=datetime.datetime.now())

	files = scrape_dir(dir.web_url)

	# Mark previously-seen-but-now-absent files as deleted, unless we're viewing the 'new files' page
	new_file_count = update_dir_records(dir, files, mark_deletions=True)

	# recursively fetch subdirs
	for (filename, is_dir, file_size) in files:
		if is_dir:
			subpath = path + filename + '/'
			if async:
				fetch_sceneorg_dir.delay(path=subpath)
			else:
				time.sleep(3)
				new_file_count += fetch_sceneorg_dir(path=subpath, async=False)

	return new_file_count

@task(time_limit=7200, ignore_result=True)
def scan_dir_listing():
	new_file_count = 0
	for path, entries in parse_all_dirs():
		# print path
		try:
			dir = Directory.objects.get(path=path)
		except Directory.DoesNotExist:
			dir = Directory.objects.create(path=path, last_seen_at=datetime.datetime.now())

		new_file_count += update_dir_records(dir, entries)

	if new_file_count > 0:
		find_sceneorg_results_files()


def update_dir_records(dir, files, mark_deletions=True):
	seen_dirs = []
	seen_files = []

	new_file_count = 0

	for (filename, is_dir, file_size) in files:
		if is_dir:
			subpath = dir.path + filename + '/'
			try:
				subdir = Directory.objects.get(path=subpath)
				subdir.last_seen_at = datetime.datetime.now()
				subdir.is_deleted = False
				subdir.save()
			except Directory.DoesNotExist:
				subdir = Directory.objects.create(
					path=subpath, last_seen_at=datetime.datetime.now(), parent=dir)
			seen_dirs.append(subdir)
		else:
			subpath = dir.path + filename
			try:
				file = File.objects.get(path=subpath)
				file.last_seen_at = datetime.datetime.now()
				file.is_deleted = False
				if file_size is not None:
					file.size = file_size
				file.save()
			except File.DoesNotExist:
				file = File.objects.create(
					path=subpath, last_seen_at=datetime.datetime.now(), directory=dir,
					size=file_size)
				new_file_count += 1
			seen_files.append(file)

	# Mark previously-seen-but-now-absent files as deleted
	if mark_deletions:
		for subdir in dir.subdirectories.filter(is_deleted=False):
			if subdir not in seen_dirs:
				subdir.mark_deleted()
		for file in dir.files.filter(is_deleted=False):
			if file not in seen_files:
				file.is_deleted = True
				file.save()
		dir.last_spidered_at = datetime.datetime.now()

	dir.last_seen_at = datetime.datetime.now()
	dir.is_deleted = False
	dir.save()

	return new_file_count
