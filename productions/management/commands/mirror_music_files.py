import time
import urllib2
from os.path import splitext

from django.core.management.base import NoArgsCommand
from django.utils.text import slugify

from mirror.actions import fetch_origin_url, FileTooBig
from productions.models import ProductionLink
from screenshots.processing import upload_to_s3


class Command(NoArgsCommand):
	"""Find remote music files suitable for mirroring on media.demozoo.org (so we can play them with cowbell)"""
	def handle_noargs(self, **options):
		links = ProductionLink.objects.filter(
			is_download_link=True,
			link_class__in=['BaseUrl', 'AmigascneFile', 'SceneOrgFile', 'FujiologyFile', 'UntergrundFile', 'PaduaOrgFile'],
			parameter__iendswith='.sid'
		).exclude(
			parameter__istartswith='https://media.demozoo.org/'
		).select_related('production')

		for prod_link in links:
			if prod_link.production.download_links.filter(parameter__istartswith='https://media.demozoo.org/').exists():
				# already mirrored
				continue

			print("prod %s: downloading from %s" % (prod_link.production_id, prod_link.url))
			try:
				download = fetch_origin_url(prod_link.url)
				sha1 = download.sha1
				(basename, file_ext) = splitext(download.filename)

				filename = 'music/' + sha1[0:2] + '/' + sha1[2:4] + '/' + slugify(basename) + file_ext
				new_url = upload_to_s3(download.as_io_buffer(), filename, file_ext, reduced_redundancy=True)
				ProductionLink.objects.create(
					production=prod_link.production,
					link_class='BaseUrl', parameter=new_url,
					is_download_link=True
				)
			except (urllib2.URLError, FileTooBig) as ex:
				pass

			time.sleep(5)
