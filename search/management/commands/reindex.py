from django.core.management.base import BaseCommand
from productions.models import Production


class Command(BaseCommand):
	help = "Re-indexes all productions"

	def handle(self, *args, **kwargs):
		for klass in (Production, ):
			i = 0
			for obj in klass.objects.prefetch_related('tags').order_by('pk'):
				obj.save()
				i += 1
				if i % 100 == 0:
					print klass, i
