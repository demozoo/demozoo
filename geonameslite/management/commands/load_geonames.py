from django.core.management.base import NoArgsCommand

import urllib2

from geonameslite.models import Country, Admin1Code, Admin2Code, Locality


class Command(NoArgsCommand):
	countries = {}
	localities = set()

	def clear_tables(self):
		print "Clearing tables"
		Country.objects.all().delete()
		Admin1Code.objects.all().delete()
		Admin2Code.objects.all().delete()
		Locality.objects.all().delete()

	def load_countries(self):
		print "Loading countries"
		objects = []
		with urllib2.urlopen('http://download.geonames.org/export/dump/countryInfo.txt') as fd:
			for line in fd:
				if line.startswith('#'):
					continue

				fields = line.split('\t')
				iso, iso3, iso_numeric, fips, name = fields[:5]
				self.countries[iso] = {}

				objects.append(Country(code=iso, name=name))
		Country.objects.bulk_create(objects)

	def load_admin1_codes(self):
		print "Loading admin level 1 codes"
		objects = []
		with urllib2.urlopen('http://download.geonames.org/export/dump/admin1CodesASCII.txt') as fd:
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
		Admin1Code.objects.bulk_create(objects)

	def load_admin2_codes(self):
		print "Loading admin level 2 codes"
		objects = []
		admin2_list = []  # to find duplicated
		skipped_duplicated = 0
		with urllib2.urlopen('http://download.geonames.org/export/dump/admin2Codes.txt') as fd:
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
				objects.append(
					Admin2Code(geonameid=geonameid, code=admin2_code, name=name,
						country_id=country_code, admin1_id=admin1_id)
				)

		Admin2Code.objects.bulk_create(objects)
		print '{0:8d} Admin2Codes loaded'.format(Admin2Code.objects.all().count())
		print '{0:8d} Admin2Codes skipped because duplicated'.format(skipped_duplicated)

	def load_localities(self):
		print 'Loading localities'
		objects = []
		batch = 10000
		processed = 0
		with open('/Users/matthew/Development/zxdemo/demozoo2/data-research/geonames/allCountries.txt', 'r') as fd:
			for line in fd:
				geonameid, name, asciiname, altnames, lat, lng, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population = line.split('\t')[:15]
				if feature_class not in ('P', 'A'):
					continue
				if country_code:
					admin1_dic = self.countries[country_code].get(admin1_code)
					if admin1_dic:
						admin1_id = admin1_dic['geonameid']
						admin2_id = admin1_dic['admins2'].get(admin2_code)
					else:
						admin1_id = None
						admin2_id = None
				else:
					country_code = None
					admin1_id = None
					admin2_id = None

				name = unicode(name, 'utf-8')
				latitude = float(lat)
				longitude = float(lng)

				if population:
					population = int(population)
				else:
					population = None

				locality = Locality(
					geonameid=geonameid,
					name=name,
					country_id=country_code,
					admin1_id=admin1_id,
					admin2_id=admin2_id,
					latitude=latitude,
					longitude=longitude,
					feature_class=feature_class,
					feature_code=feature_code,
					population=population)
				objects.append(locality)
				processed += 1
				self.localities.add(geonameid)

				if processed % batch == 0:
					Locality.objects.bulk_create(objects)
					print "{0:8d} Localities loaded".format(processed)
					objects = []

		Locality.objects.bulk_create(objects)
		print "{0:8d} Localities loaded".format(processed)


	def handle_noargs(self, **options):
		self.clear_tables()
		self.load_countries()
		self.load_admin1_codes()
		self.load_admin2_codes()

		# code for reloading country / admin1 / admin2 structs from the db if skipping load_countries / load_admin(1|2)_codes:
		#for country in Country.objects.all():
		#	self.countries[country.code] = {}
		#for admin1 in Admin1Code.objects.all():
		#	self.countries[admin1.country_id][admin1.code] = {'geonameid': admin1.geonameid, 'admins2': {}}
		#for admin2 in Admin2Code.objects.filter(admin1__isnull=False).select_related('admin1'):
		#	admin1_dic = self.countries[admin2.country_id].get(admin2.admin1.code)
		#	if admin1_dic:
		#		admin1_dic['admins2'][admin2.code] = admin2.geonameid
		self.load_localities()
