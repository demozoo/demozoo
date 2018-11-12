from django.core.management.base import BaseCommand
from parties.models import Party
from demoscene.models import NickVariant, Releaser
from productions.models import Production


class Command(BaseCommand):
	help = "Re-indexes all productions"

	def handle(self, *args, **kwargs):
		BATCH_SIZE = 10000

		for klass in (NickVariant, Party, Releaser, Production):
			i = 0
			while True:
				qs = klass.objects.order_by('pk')
				if hasattr(klass, 'tags'):
					qs = qs.prefetch_related('tags')
				batch = qs[i:(i + BATCH_SIZE)]

				for obj in batch:
					obj.save()
					i += 1
					if i % 100 == 0:
						print klass, i

				if len(batch) < BATCH_SIZE:
					break
