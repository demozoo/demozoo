import csv

from django.http import HttpResponse

from productions.models import Production
from platforms.models import Platform


def demos(request):
	# ZX Spectrum productions (non graphics/music) with download links
	# and author nationalities

	zx_spectrum = Platform.objects.get(name='ZX Spectrum')

	prods = Production.objects.filter(
		supertype='production',
		platforms=zx_spectrum,
	).prefetch_related(
		'types', 'platforms',
		'author_nicks', 'author_affiliation_nicks', 'links',
		'author_nicks__releaser', 'credits__nick__releaser'
	).order_by('title')

	response = HttpResponse(mimetype='text/plain;charset=utf-8')
	csvfile = csv.writer(response)
	csvfile.writerow([
		'ID', 'Demozoo URL', 'Title', 'By', 'Release date', 'Type', 'Nationality', 'Download URL'
	])
	for prod in prods:
		prod_types = sorted(prod.types.all(), key=lambda t: t.name)
		nationalities = set([nick.releaser.country_code for nick in prod.author_nicks.all()]).union([credit.nick.releaser.country_code for credit in prod.credits.all()])
		nationalities = list(n for n in nationalities if n)
		csvfile.writerow([
			prod.id,
			(u'http://demozoo.org' + prod.get_absolute_url()).encode('utf-8'),
			prod.title.encode('utf-8'),
			prod.byline_string.encode('utf-8'),
			prod.release_date.numeric_format() if prod.release_date else '',
			', '.join([typ.name for typ in prod_types]).encode('utf-8'),
			' / '.join(nationalities),
			' / '.join([link.download_url for link in prod.links.all() if link.is_download_link]).encode('utf-8'),
		])

	return response
