from demoscene.shortcuts import *
from demoscene.models import Party, PartySeries, Competition
from demoscene.forms.party import *

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

@login_required
def add_competition(request, party_id):
	party = get_object_or_404(Party, id = party_id)
	competition = Competition(party = party)
	if request.method == 'POST':
		form = CompetitionForm(request.POST, instance = competition)
		if form.is_valid():
			form.save()
			# TODO: party updated_at datestamps
			# party.updated_at = datetime.datetime.now()
			# party.save()
			if request.POST.get('enter_results'):
				return redirect('party_edit_competition', args = [party.id, competition.id])
			else:
				return HttpResponseRedirect(party.get_absolute_url())
	else:
		form = CompetitionForm(instance = competition)
	return ajaxable_render(request, 'parties/add_competition.html', {
		'party': party,
		'form': form,
	})

@login_required
def edit_competition(request, party_id, competition_id):
	party = get_object_or_404(Party, id = party_id)
	competition = get_object_or_404(Competition, party = party, id = competition_id)
	if request.method == 'POST':
		competition_form = CompetitionForm(request.POST, instance = competition)
		formset = CompetitionPlacingFormset(request.POST, instance = competition)
		if competition_form.is_valid() and formset.is_valid():
			def form_order_key(form):
				if form.is_valid():
					return form.cleaned_data['ORDER'] or 9999
				else:
					return 9999
			
			sorted_forms = sorted(formset.forms, key = form_order_key)
			for (i, form) in enumerate(sorted_forms):
				form.instance.position = i+1
			formset.save()
			# TODO: competition/party updated_at datestamps
			#competition.updated_at = datetime.datetime.now()
			competition_form.save()
			return redirect('party', args = [party.id])
	else:
		competition_form = CompetitionForm(instance = competition)
		formset = CompetitionPlacingFormset(instance = competition)
	return ajaxable_render(request, 'parties/edit_competition.html', {
		'party': party,
		'competition': competition,
		'formset': formset,
		'competition_form': competition_form,
	})
