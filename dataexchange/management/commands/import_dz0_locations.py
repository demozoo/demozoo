# Import scener locations from Demozoo v0 MySQL database

from django.core.management.base import NoArgsCommand

import sys
from geocode import geocode
from demoscene.models import *
from dataexchange import demozoo0


class Command(NoArgsCommand):

	def handle_noargs(self, **options):
		import codecs
		sys.stdout = codecs.getwriter('utf8')(sys.stdout)

		geocoded_locations = {}

		for releaser_info in demozoo0.sceners_with_locations():

			for releaser in Releaser.objects.filter(demozoo0_id=releaser_info['id']):
				if releaser.location:
					continue

				if releaser_info['location'] in geocoded_locations:
					location = geocoded_locations[releaser_info['location']]
				else:
					location = geocode(releaser_info['location'])
					geocoded_locations[releaser_info['location']] = location
					print "looked up %s, got %s as response" % (releaser_info['location'], location['location'])

				if location:
					releaser.location = location['location']
					releaser.country_code = location['country_code'] or ''
					releaser.latitude = location['latitude']
					releaser.longitude = location['longitude']
					releaser.woe_id = location['woeid']
					releaser.save()

				print "set location of %s to %s" % (releaser.name, releaser.location)

				sys.stdout.flush()
