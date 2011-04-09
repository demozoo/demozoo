from demoscene.shortcuts import *
from django.contrib.auth.decorators import login_required
from demoscene.models import Production

def index(request):
	if not request.user.is_staff:
		return redirect('home')
	return render(request, 'maintenance/index.html')

def prods_without_screenshots(request):
	productions = Production.objects \
		.filter(screenshots__id__isnull = True) \
		.exclude(supertype = 'music').order_by('title')
	return render(request, 'maintenance/report.html', {
		'title': 'Productions without screenshots',
		'productions': productions
	})

def prods_without_external_links(request):
	filters = {}
	for field in Production.external_site_ref_field_names:
		filters["%s__isnull" % field] = True
	
	productions = Production.objects \
		.filter(supertype = 'production', **filters) \
		.order_by('title')
	return render(request, 'maintenance/report.html', {
		'title': 'Productions without external links',
		'productions': productions,
	})

def prods_without_release_date(request):
	productions = Production.objects.filter(release_date_date__isnull = True)
	return render(request, 'maintenance/report.html', {
		'title': 'Productions without a release date',
		'productions': productions,
	})

def prods_without_release_date_with_placement(request):
	productions = Production.objects.filter(release_date_date__isnull = True, competition_placings__isnull = False)
	return render(request, 'maintenance/report.html', {
		'title': 'Productions without a release date but with a party placement attached',
		'productions': productions,
	})

def prod_soundtracks_without_release_date(request):
	productions = Production.objects.filter(appearances_as_soundtrack__isnull = False, release_date_date__isnull = True)
	return render(request, 'maintenance/report.html', {
		'title': 'Music with productions attached but no release date',
		'productions': productions,
	})
