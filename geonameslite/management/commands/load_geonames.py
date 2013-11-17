from django.core.management.base import NoArgsCommand

import urllib2

from geonameslite.models import Country


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		print "Clearing tables"
		Country.objects.all().delete()

		print "Loading countries"
		f = urllib2.urlopen('http://download.geonames.org/export/dump/countryInfo.txt')
		for line in f:
			if line.startswith('#'):
				continue

			fields = line.split('\t')
			iso, iso3, iso_numeric, fips, name = fields[:5]

			Country.objects.create(code=iso, name=name)

		f.close()
