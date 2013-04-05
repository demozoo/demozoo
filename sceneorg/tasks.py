from celery.task import task
from sceneorg.models import Directory, File, FileTooBig
from sceneorg.scraper import scrape_dir, scrape_new_files_dir
import datetime

@task(rate_limit = '6/m', ignore_result = True)
def fetch_sceneorg_dir(path, days = None):
	try:
		dir = Directory.objects.get(path = path)
	except Directory.DoesNotExist:
		dir = Directory.objects.create(path = path, last_seen_at = datetime.datetime.now())
	
	if days:
		files = scrape_new_files_dir(dir.new_files_url(days))
	else:
		files = scrape_dir(dir.web_url)
	
	seen_dirs = []
	seen_files = []
	
	for (filename, is_dir) in files:
		if is_dir:
			subpath = path + filename + '/'
			try:
				subdir = Directory.objects.get(path = subpath)
				subdir.last_seen_at = datetime.datetime.now()
				subdir.save()
			except Directory.DoesNotExist:
				subdir = Directory.objects.create(
					path = subpath, last_seen_at = datetime.datetime.now(), parent = dir)
			seen_dirs.append(subdir)
			fetch_sceneorg_dir.delay(path = subpath, days = days)
		else:
			subpath = path + filename
			try:
				file = File.objects.get(path = subpath)
				file.last_seen_at = datetime.datetime.now()
				file.is_deleted = False
				file.save()
			except File.DoesNotExist:
				file = File.objects.create(
					path = subpath, last_seen_at = datetime.datetime.now(), directory = dir)
			seen_files.append(file)
	
	# Mark previously-seen-but-now-absent files as deleted, unless we're viewing the 'new files' page
	if not days:
		for subdir in dir.subdirectories.filter(is_deleted = False):
			if subdir not in seen_dirs:
				subdir.mark_deleted()
		for file in dir.files.filter(is_deleted = False):
			if file not in seen_files:
				file.is_deleted = True
				file.save()
		dir.last_spidered_at = datetime.datetime.now()
	
	dir.last_seen_at = datetime.datetime.now()
	dir.save()

@task(rate_limit = '6/m', ignore_result = True)
def fetch_sceneorg_file(file_id):
	try:
		File.objects.get(id=file_id).fetch()
	except FileTooBig:
		pass
