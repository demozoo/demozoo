from productions.models import Credit
from django.core.management.base import NoArgsCommand
import re


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		credits = Credit.objects.filter(category='')
		for credit in credits:
			print credit
			# extract a list of (category, detail) tuples
			credit_components = re.findall(r'(Code|Music|Graphics|Other)(?: \(([^\)]+)\))?', credit.role, re.I)

			if not credit_components:
				raise Exception('No credit components found in the standard format for credit %d: %s' % (credit.id, credit.role))

			# insert new credit records for the second and subsequent components
			for (category, detail) in credit_components[1:]:
				Credit.objects.create(
					production=credit.production,
					nick=credit.nick,
					category=category.capitalize(),
					role=detail
				)

			# replace the existing credit record with an entry for the first component
			(category, detail) = credit_components[0]
			credit.category = category.capitalize()
			credit.role = detail
			credit.save()
