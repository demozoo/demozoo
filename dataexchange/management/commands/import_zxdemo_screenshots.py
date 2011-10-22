from django.core.management.base import BaseCommand
from demoscene.models import Production, Screenshot
from django.core.files import File
import os

import pymysql

class Command(BaseCommand):
	args = 'path/to/zxdemo/screens/full'
	help = 'Import screenshots from zxdemo'
	def handle(self, *args, **options):
		image_dir = args[0]
		connection = pymysql.connect(user="root", db="zxdemo")
		cur = connection.cursor()
		cur.execute("SELECT item_id, img from screenshot")
		for item_id, image_filename in cur:
			try:
				production = Production.objects.get(zxdemo_id = item_id)
			except Production.DoesNotExist, Production.MultipleObjectsReturned:
				print "Skipping production %s - missing or duplicate entries"
				continue
			print "%s - %s" % (production.id, production.title)
			screenshot = Screenshot(production = production)
			full_filename = os.path.join(image_dir, image_filename)
			f = File(open(full_filename))
			screenshot.original.save(os.path.basename(image_filename), f)
