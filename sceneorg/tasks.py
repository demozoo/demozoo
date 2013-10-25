from celery.task import task
from sceneorg.models import Directory, File, FileTooBig
from sceneorg.scraper import scrape_dir, scrape_new_files_dir
from sceneorg.dirparser import parse_all_dirs
import datetime


@task(rate_limit='6/m', ignore_result=True)
def fetch_sceneorg_dir(path, days=None):
	try:
		dir = Directory.objects.get(path=path)
	except Directory.DoesNotExist:
		dir = Directory.objects.create(path=path, last_seen_at=datetime.datetime.now())

	if days:
		files = scrape_new_files_dir(dir.new_files_url(days))
	else:
		files = scrape_dir(dir.web_url)

	# Mark previously-seen-but-now-absent files as deleted, unless we're viewing the 'new files' page
	update_dir_records(dir, files, mark_deletions=(not days))

	# recursively fetch subdirs
	for (filename, is_dir) in files:
		if is_dir:
			subpath = path + filename + '/'
			fetch_sceneorg_dir.delay(path=subpath, days=days)

def scan_dir_listing(filename):
	for path, entries in parse_all_dirs(filename):
		print path
		try:
			dir = Directory.objects.get(path=path)
		except Directory.DoesNotExist:
			dir = Directory.objects.create(path=path, last_seen_at=datetime.datetime.now())

		update_dir_records(dir, entries)


def update_dir_records(dir, files, mark_deletions=True):
	seen_dirs = []
	seen_files = []

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


@task(rate_limit='6/m', ignore_result=True)
def fetch_sceneorg_file(file_id):
	try:
		File.objects.get(id=file_id).fetch()
	except FileTooBig:
		pass
