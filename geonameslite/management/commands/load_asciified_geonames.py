from django.core.management.base import NoArgsCommand

from geonameslite.models import Locality, AlternateName
from unidecode import unidecode

class Command(NoArgsCommand):
	def clear_tables(self):
		AlternateName.objects.filter(is_asciified=True).delete()

	names = {}
	def load_initial_names(self):
		batch = 100000
		print "Loading existing locations"
		loaded = 0
		for loc in Locality.objects.all():
			self.names[loc.geonameid] = set([loc.name])
			loaded += 1
			if loaded % batch == 0:
				print "{0:8d} locations loaded".format(loaded)

		print "Loading existing alt names"
		loaded = 0
		for alt_name in AlternateName.objects.all():
			self.names[alt_name.locality_id].add(alt_name.name)
			loaded += 1
			if loaded % batch == 0:
				print "{0:8d} alt names loaded".format(loaded)

	def load_localities(self):
		print "ASCIIfying locality names"
		objects = []
		batch = 10000
		processed = 0
		for locality in Locality.objects.all():
			name = unidecode(locality.name)
			if name != locality.name and name not in self.names[locality.geonameid]:
				objects.append(AlternateName(
					locality_id=locality.geonameid,
					name=name,
					is_asciified=True
				))
				self.names[locality.geonameid].add(name)
				processed += 1

				if processed % batch == 0:
					AlternateName.objects.bulk_create(objects)
					print "{0:8d} locality names ASCIIfied".format(processed)
					objects = []

		AlternateName.objects.bulk_create(objects)
		print "{0:8d} locality names ASCIIfied".format(processed)

	def load_altnames(self):
		print "ASCIIfying alt names"
		objects = []
		batch = 10000
		processed = 0
		for alt_name in AlternateName.objects.all():
			name = unidecode(alt_name.name)
			if name != alt_name.name and name not in self.names[alt_name.locality_id]:
				objects.append(AlternateName(
					locality_id=alt_name.locality_id,
					name=name,
					is_asciified=True
				))
				self.names[alt_name.locality_id].add(name)
				processed += 1

				if processed % batch == 0:
					AlternateName.objects.bulk_create(objects)
					print "{0:8d} alt names ASCIIfied".format(processed)
					objects = []

		AlternateName.objects.bulk_create(objects)
		print "{0:8d} alt names ASCIIfied".format(processed)

	def handle_noargs(self, **options):
		self.clear_tables()
		self.load_initial_names()
		self.load_localities()
		self.load_altnames()
