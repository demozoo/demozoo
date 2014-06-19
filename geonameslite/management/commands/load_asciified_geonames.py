from django.core.management.base import NoArgsCommand
from django.db.models import Max

from geonameslite.models import Locality, AlternateName
from unidecode import unidecode

class Command(NoArgsCommand):
	def clear_tables(self):
		AlternateName.objects.filter(is_asciified=True).delete()

	def load_localities(self):
		print "ASCIIfying locality names"
		batch_size = 10000
		processed = 0

		max_id = Locality.objects.aggregate(Max('geonameid'))['geonameid__max']
		batch_start = 0

		while batch_start <= max_id:
			names = {}
			objects = []

			for locality in Locality.objects.filter(geonameid__gte=batch_start, geonameid__lt=batch_start + batch_size):
				names.setdefault(locality.geonameid, set())
				name = unidecode(locality.name)
				if (
					name != locality.name
					and name not in names[locality.geonameid]
					and not Locality.objects.filter(geonameid=locality.geonameid, name=name).exists()
					and not AlternateName.objects.filter(locality_id=locality.geonameid, name=name).exists()
					):

					objects.append(AlternateName(
						locality_id=locality.geonameid,
						name=name,
						is_asciified=True
					))
					names[locality.geonameid].add(name)
					processed += 1

			AlternateName.objects.bulk_create(objects)
			print "{0:8d} locality names ASCIIfied".format(processed)

			batch_start += batch_size

		AlternateName.objects.bulk_create(objects)
		print "{0:8d} locality names ASCIIfied".format(processed)

	def load_altnames(self):
		print "ASCIIfying alt names"
		batch_size = 10000
		processed = 0

		max_id = AlternateName.objects.aggregate(Max('id'))['id__max']
		batch_start = 0

		while batch_start <= max_id:
			names = {}
			objects = []

			for alt_name in AlternateName.objects.filter(id__gte=batch_start, id__lt=batch_start + batch_size):
				names.setdefault(alt_name.locality_id, set())
				name = unidecode(alt_name.name)
				if (
					name != alt_name.name
					and name not in names[alt_name.locality_id]
					and not Locality.objects.filter(geonameid=alt_name.locality_id, name=name).exists()
					and not AlternateName.objects.filter(locality_id=alt_name.locality_id, name=name).exists()
					):
					objects.append(AlternateName(
						locality_id=alt_name.locality_id,
						name=name,
						is_asciified=True
					))
					names[alt_name.locality_id].add(name)
					processed += 1

			AlternateName.objects.bulk_create(objects)
			print "{0:8d} alt names ASCIIfied".format(processed)
			batch_start += batch_size

		AlternateName.objects.bulk_create(objects)
		print "{0:8d} alt names ASCIIfied".format(processed)

	def handle_noargs(self, **options):
		self.clear_tables()
		self.load_localities()
		self.load_altnames()
