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
	return render(request, 'maintenance/prods_without_screenshots.html', {
		'productions': productions
	})

def prods_without_external_links(request):
	filters = {}
	for field in Production.external_site_ref_field_names:
		filters["%s__isnull" % field] = True
	
	productions = Production.objects \
		.filter(supertype = 'production', **filters) \
		.order_by('title')
	return render(request, 'maintenance/prods_without_external_links.html', {
		'productions': productions
	})
