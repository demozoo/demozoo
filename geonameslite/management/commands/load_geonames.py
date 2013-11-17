from django.core.management.base import NoArgsCommand

import urllib2

from geonameslite.models import Country, Admin1Code, Admin2Code


class Command(NoArgsCommand):
	countries = {}

	def clear_tables(self):
		print "Clearing tables"
		Country.objects.all().delete()
		Admin1Code.objects.all().delete()
		Admin2Code.objects.all().delete()

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

	def load_admin2_codes(self):
		print "Loading admin level 2 codes"
		objects = []
		admin2_list = []  # to find duplicated
		skipped_duplicated = 0
		fd = urllib2.urlopen('http://download.geonames.org/export/dump/admin2Codes.txt')
		for line in fd:
			fields = line[:-1].split('\t')
			codes, name = fields[0:2]
			country_code, admin1_code, admin2_code = codes.split('.')

			# if there is a duplicated
			long_code = "{}.{}.{}".format(country_code, admin1_code, name)
			if long_code in admin2_list:
				skipped_duplicated += 1
				continue

			admin2_list.append(long_code)

			geonameid = fields[3]
			admin1_dic = self.countries[country_code].get(admin1_code)

			# if there is not admin1 level we save it but we don't keep it for the localities
			if admin1_dic is None:
				admin1_id = None
			else:
				# If not, we get the id of admin1 and we save geonameid for filling in Localities later
				admin1_id = admin1_dic['geonameid']
				admin1_dic['admins2'][admin2_code] = geonameid

			name = unicode(name, 'utf-8')
			objects.append(Admin2Code(geonameid=geonameid,
									  code=admin2_code,
									  name=name,
									  country_id=country_code,
									  admin1_id=admin1_id))

		fd.close()

		Admin2Code.objects.bulk_create(objects)
		print '{0:8d} Admin2Codes loaded'.format(Admin2Code.objects.all().count())
		print '{0:8d} Admin2Codes skipped because duplicated'.format(skipped_duplicated)

	def handle_noargs(self, **options):
		self.clear_tables()
		self.load_countries()
		self.load_admin1_codes()
		self.load_admin2_codes()
