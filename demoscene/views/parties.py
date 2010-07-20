from demoscene.shortcuts import *
from demoscene.models import Party, PartySeries
from demoscene.forms import PartyForm, EditPartyForm

from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

@login_required
def create(request):
	if request.method == 'POST':
		party = Party()
		form = PartyForm(request.POST, instance = party)
		if form.is_valid():
			if form.cleaned_data['new_party_series_name']:
				party_series = PartySeries(name = form.cleaned_data['new_party_series_name'])
				party_series.save()
			else:
				party_series = form.cleaned_data['existing_party_series']
			party.party_series = party_series
			form.save()
			messages.success(request, 'Party added')
			return redirect('party', args = [party.id])
	else:
		form = PartyForm()
	return render(request, 'parties/create.html', {
		'form': form,
	})

@login_required
def edit(request, party_id):
	party = get_object_or_404(Party, id = party_id)
	if request.method == 'POST':
		form = EditPartyForm(request.POST, instance = party)
		if form.is_valid():
			form.save()
			messages.success(request, 'Party updated')
			return redirect('party', args = [party.id])
	else:
		form = EditPartyForm(instance = party)
	
	return render(request, 'parties/edit.html', {
		'party': party,
		'form': form,
	})
