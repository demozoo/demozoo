from django.core.management.base import BaseCommand
from productions.models import Production


class Command(BaseCommand):
	help = "Re-indexes all productions"

	def handle(self, *args, **kwargs):
		BATCH_SIZE = 10000

		for klass in (Production, ):
			i = 0
			while True:
				batch = klass.objects.prefetch_related('tags').order_by('pk')[i:(i + BATCH_SIZE)]
				for obj in batch:
					obj.save()
					i += 1
					if i % 100 == 0:
						print klass, i

				if len(batch) < BATCH_SIZE:
					break
