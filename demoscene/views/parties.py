from demoscene.shortcuts import *
from demoscene.models import Party, PartySeries

def index(request):
	party_series = PartySeries.objects.order_by('name')
	return render(request, 'parties/index.html', {
		'party_series': party_series,
	})

def show(request, party_id):
	party = Party.objects.get(id = party_id)
	return render(request, 'parties/show.html', {
		'party': party,
	})

def show_series(request, party_series_id):
	party_series = PartySeries.objects.get(id = party_series_id)
	return render(request, 'parties/show_series.html', {
		'party_series': party_series,
	})
