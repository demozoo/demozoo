import csv

from django.http import HttpResponse

from demoscene.models import Releaser


def group_abbreviations(request):
	groups = Releaser.objects.filter(is_group=True).prefetch_related('nicks').order_by('name')

	response = HttpResponse(content_type='text/plain;charset=utf-8')
	csvfile = csv.writer(response)
	csvfile.writerow([
		'ID', 'Demozoo URL', 'Name', 'Differentiator', 'Abbreviation'
	])
	for group in groups:
		csvfile.writerow([
			group.id,
			(u'https://demozoo.org' + group.get_absolute_url()).encode('utf-8'),
			group.name.encode('utf-8'),
			group.primary_nick.differentiator.encode('utf-8'),
			group.abbreviation.encode('utf-8'),
		])

	return response
