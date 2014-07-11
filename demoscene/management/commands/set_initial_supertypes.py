from productions.models import Production
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for prod in Production.objects.all():
			prod.save() # save() trigger will sync with inferred supertype. Gosh, that was easy.
