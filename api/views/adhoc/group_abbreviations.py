import csv

from django.http import HttpResponse

from demoscene.models import Nick


def group_abbreviations(request):
	nicks = Nick.objects.filter(releaser__is_group=True).select_related('releaser').prefetch_related('variants').order_by('name')

	response = HttpResponse(content_type='text/plain;charset=utf-8')
	csvfile = csv.writer(response)
	csvfile.writerow([
		'ID', 'Demozoo URL', 'Name', 'Differentiator', 'Abbreviation', 'Other variants'
	])
	for nick in nicks:
		csvfile.writerow([
			nick.releaser.id,
			(u'https://demozoo.org' + nick.releaser.get_absolute_url()).encode('utf-8'),
			nick.name.encode('utf-8'),
			nick.differentiator.encode('utf-8'),
			nick.abbreviation.encode('utf-8'),
			nick.nick_variant_list.encode('utf-8')
		])

	return response
