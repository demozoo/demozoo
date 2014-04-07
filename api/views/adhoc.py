from django.utils import simplejson
from django.http import HttpResponse
from demoscene.models import Credit, Production

from itertools import groupby
import datetime
import csv

def pouet_credits(request):
	# Retrieve productions with Pouet IDs with credits for releasers who have Pouet user IDs
	credits = Credit.objects.raw('''
		SELECT
			demoscene_credit.id,
			demoscene_productionlink.parameter AS pouet_prod_id,
			demoscene_releaserexternallink.parameter AS pouet_user_id,
			demoscene_credit.category,
			demoscene_credit.role
		FROM
			demoscene_credit
			INNER JOIN demoscene_productionlink ON (
				demoscene_credit.production_id = demoscene_productionlink.production_id
				AND demoscene_productionlink.link_class = 'PouetProduction'
			)
			INNER JOIN demoscene_nick ON (
				demoscene_credit.nick_id = demoscene_nick.id
			)
			INNER JOIN demoscene_releaserexternallink ON (
				demoscene_nick.releaser_id = demoscene_releaserexternallink.releaser_id
				AND demoscene_releaserexternallink.link_class = 'SceneidAccount'
			)
		ORDER BY
			pouet_prod_id, pouet_user_id, category
	''')

	credits_json = [
		{
			'pouet_prod_id': prod_id,
			'pouet_user_id': user_id,
			'role': ', '.join([
				("%s (%s)" % (cred.category, cred.role)) if cred.role else cred.category
				for cred in creds
			]),
		}
		for ((prod_id, user_id), creds) in groupby(credits, lambda c: (c.pouet_prod_id, c.pouet_user_id))
	]

	return HttpResponse(simplejson.dumps(credits_json), mimetype="text/javascript")


def get_month_parameter(request):
	"""helper function for klubi_demoshow and scenesat_monthly:
	extract a 'month' param from the request and return start_date/end date"""
	try:
		start_date = datetime.datetime.strptime(request.GET['month'], '%Y-%m').date()
	except (KeyError, ValueError):
		this_month = datetime.date.today().replace(day=1)
		# find last month by subtracting 7 days from start of this month, and taking
		# first day of the resulting month. ugh.
		start_date = (this_month - datetime.timedelta(days=7)).replace(day=1)

	# there must be a less horrible way to add one month, surely...?
	end_date = (start_date + datetime.timedelta(days=40)).replace(day=1)

	return (start_date, end_date)


def klubi_demoshow(request):
	# Get a list of prods released in the given calendar month
	# (default: the calendar month just gone)
	# that are of supertype production (= not music or gfx)
	# and not only of type diskmag or tool

	(start_date, end_date) = get_month_parameter(request)

	prods = Production.objects.filter(
		supertype='production',
		release_date_date__gte=start_date, release_date_date__lt=end_date,
	).exclude(release_date_precision='y').prefetch_related(
		'types', 'platforms',
		'author_nicks', 'author_affiliation_nicks',
	).order_by('release_date_date')

	# put videos (wilds) into a separate list after the main one
	exe_prods = []
	video_prods = []

	for prod in prods:
		if prod.types.count() == 0:
			# don't know what type it is, so include it to be on the safe side
			exe_prods.append(prod)
			continue

		# strip out types that are not really suitable for a demo show
		interesting_types = [typ for typ in prod.types.all() if typ.name not in ('Diskmagazine', 'Tool', 'Game')]

		if len(interesting_types) == 0:
			pass

		elif len(interesting_types) == 1 and interesting_types[0].name == 'Video':
			video_prods.append(prod)
		else:
			exe_prods.append(prod)

	response = HttpResponse(mimetype='text/plain;charset=utf-8')
	csvfile = csv.writer(response)
	csvfile.writerow([
		'Demozoo URL', 'Title', 'By', 'Release date', 'Type', 'Platform', 'Download URL', 'Video URL'
	])
	for prod in exe_prods + video_prods:
		platforms = sorted(prod.platforms.all(), key=lambda p:p.name)
		prod_types = sorted(prod.types.all(), key=lambda t:t.name)
		csvfile.writerow([
			(u'http://demozoo.org' + prod.get_absolute_url()).encode('utf-8'),
			prod.title.encode('utf-8'),
			prod.byline_string.encode('utf-8'),
			prod.release_date,
			', '.join([typ.name for typ in prod_types]).encode('utf-8'),
			', '.join([platform.name for platform in platforms]).encode('utf-8'),
			' / '.join([link.download_url for link in prod.links.all() if link.is_download_link]).encode('utf-8'),
			' / '.join([link.download_url for link in prod.links.all() if link.is_streaming_video]).encode('utf-8'),
		])

	return response


def scenesat_monthly(request):
	# Get a list of music released in the given calendar month
	# (default: the calendar month just gone)

	(start_date, end_date) = get_month_parameter(request)

	prods = Production.objects.filter(
		supertype='music',
		release_date_date__gte=start_date, release_date_date__lt=end_date,
	).exclude(release_date_precision='y').prefetch_related(
		'types', 'platforms',
		'author_nicks', 'author_affiliation_nicks',
	).order_by('release_date_date')

	response = HttpResponse(mimetype='text/plain;charset=utf-8')
	csvfile = csv.writer(response)
	csvfile.writerow([
		'Demozoo URL', 'Title', 'By', 'Release date', 'Type', 'Platform', 'Download URL'
	])
	for prod in prods:
		platforms = sorted(prod.platforms.all(), key=lambda p:p.name)
		prod_types = sorted(prod.types.all(), key=lambda t:t.name)
		csvfile.writerow([
			(u'http://demozoo.org' + prod.get_absolute_url()).encode('utf-8'),
			prod.title.encode('utf-8'),
			prod.byline_string.encode('utf-8'),
			prod.release_date,
			', '.join([typ.name for typ in prod_types]).encode('utf-8'),
			', '.join([platform.name for platform in platforms]).encode('utf-8'),
			' / '.join([link.download_url for link in prod.links.all() if link.is_download_link]).encode('utf-8'),
		])

	return response
