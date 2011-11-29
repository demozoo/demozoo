from celery.task import task
from sceneorg.models import Directory, File
from sceneorg.scraper import scrape_dir
import datetime

@task(rate_limit = '6/m', ignore_result = True)
def fetch_sceneorg_dir(path):
	try:
		dir = Directory.objects.get(path = path)
	except Directory.DoesNotExist:
		dir = Directory.objects.create(path = path, last_seen_at = datetime.datetime.now())
	
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
			fetch_sceneorg_dir.delay(path = subpath)
		else:
			subpath = path + filename
			try:
				file = File.objects.get(path = subpath)
				file.last_seen_at = datetime.datetime.now()
				file.save()
			except File.DoesNotExist:
				file = File.objects.create(
					path = subpath, last_seen_at = datetime.datetime.now(), directory = dir)
			seen_files.append(file)
	
	for subdir in dir.subdirectories.filter(is_deleted = False):
		if subdir not in seen_dirs:
			subdir.is_deleted = True
			subdir.save()
	for file in dir.files.filter(is_deleted = False):
		if file not in seen_files:
			file.is_deleted = True
			file.save()
	
	dir.last_seen_at = datetime.datetime.now()
	dir.last_spidered_at = datetime.datetime.now()
	dir.save()
