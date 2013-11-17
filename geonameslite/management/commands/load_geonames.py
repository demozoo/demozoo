from django.core.management.base import NoArgsCommand

import urllib2

from geonameslite.models import Country, Admin1Code


class Command(NoArgsCommand):
	countries = {}

	def clear_tables(self):
		print "Clearing tables"
		Country.objects.all().delete()
		Admin1Code.objects.all().delete()

	def load_countries(self):
		print "Loading countries"
		objects = []
		fd = urllib2.urlopen('http://download.geonames.org/export/dump/countryInfo.txt')
		for line in fd:
			if line.startswith('#'):
				continue

			fields = line.split('\t')
			iso, iso3, iso_numeric, fips, name = fields[:5]
			self.countries[iso] = {}

			objects.append(Country(code=iso, name=name))
		fd.close()
		Country.objects.bulk_create(objects)

	def load_admin1_codes(self):
		print "Loading admin level 1 codes"
		objects = []
		fd = urllib2.urlopen('http://download.geonames.org/export/dump/admin1CodesASCII.txt')
		for line in fd:
			fields = line[:-1].split('\t')
			codes, name = fields[0:2]
			country_code, admin1_code = codes.split('.')
			geonameid = fields[3]
			self.countries[country_code][admin1_code] = {'geonameid': geonameid, 'admins2': {}}
			name = unicode(name, 'utf-8')
			objects.append(Admin1Code(geonameid=geonameid,
				code=admin1_code,
				name=name,
				country_id=country_code))
		fd.close()
		Admin1Code.objects.bulk_create(objects)

	def handle_noargs(self, **options):
		self.clear_tables()
		self.load_countries()
		self.load_admin1_codes()
