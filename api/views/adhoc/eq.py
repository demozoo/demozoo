import csv

from django.http import HttpResponse

from demoscene.models import Releaser
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
		# try to assemble a list of nationalities based on the sceners listed under authors or credits
		authors = [nick.releaser for nick in prod.author_nicks.all()]
		credited_sceners = [credit.nick.releaser for credit in prod.credits.all()]
		nationalities = set([author.country_code for author in authors]).union([scener.country_code for scener in credited_sceners])
		nationalities = list(n for n in nationalities if n)
		# if this results in an empty list, see if it's entirely written by groups whose members all belong to one country
		if (not nationalities) and all(author.is_group for author in authors):
			members = Releaser.objects.filter(group_memberships__group__in=authors)
			nationalities = list(set([member.country_code for member in members]))
			if len(nationalities) != 1 or nationalities[0] == '':
				nationalities = []

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
