from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponse
from django.contrib import messages

from demoscene.models import Party, Competition
from sceneorg.models import Directory


@login_required
def compofolders(request):
	parties = Party.objects.filter(external_links__link_class='SceneOrgFolder')

	# only include parties with at least one competition entered
	parties = parties.annotate(num_compos=Count('competitions')).filter(num_compos__gt=0)

	if request.GET.get('order') == 'series':
		parties = parties.select_related('party_series').order_by('party_series__name', 'start_date_date')
		return render(request, 'sceneorg/compofolders/parties_by_series.html', {
			'parties': parties,
		})
	else:
		parties = parties.extra(
			select={'date_year': "DATE_TRUNC('year', start_date_date)"},
			order_by=['date_year', 'name']
		)
		return render(request, 'sceneorg/compofolders/parties_by_year.html', {
			'parties': parties,
		})


@login_required
def compofolder_party(request, party_id):
	party = get_object_or_404(Party, id=party_id)
	sceneorg_paths = [link.parameter for link in party.external_links.filter(link_class='SceneOrgFolder')]

	query = Q(path__startswith=sceneorg_paths[0])
	for path in sceneorg_paths[1:]:
		query = query | Q(path__startswith=path)

	dirs = Directory.objects.filter(query).order_by('path').prefetch_related('competitions')
	unmatched_competitions = party.competitions.annotate(num_dirs=Count('sceneorg_directories')).filter(num_dirs=0)
	unmatched_dirs = [d for d in dirs if d.competitions.count() == 0]
	matched_dirs = [d for d in dirs if d.competitions.count() > 0]

	return render(request, 'sceneorg/compofolders/party.html', {
		'party': party,
		'unmatched_directories': unmatched_dirs,
		'unmatched_competitions': unmatched_competitions,
		'matched_directories': matched_dirs,
	})


@login_required
def compofolder_link(request):
	directory = get_object_or_404(Directory, id=request.POST.get('directory_id'))
	competition = get_object_or_404(Competition, id=request.POST.get('competition_id'))

	competition.sceneorg_directories.add(directory)

	return HttpResponse("OK", content_type="text/plain")


@login_required
def compofolder_unlink(request):
	directory = get_object_or_404(Directory, id=request.POST.get('directory_id'))
	competition = get_object_or_404(Competition, id=request.POST.get('competition_id'))

	competition.sceneorg_directories.remove(directory)

	return HttpResponse("OK", content_type="text/plain")


@login_required
def compofolders_done(request, party_id):
	party = get_object_or_404(Party, id=party_id)
	if request.method == 'POST':
		party.sceneorg_compofolders_done = True
		party.save()
		messages.success(request, 'Compo folders for %s marked as done. Thanks!' % party.name)
	return redirect('sceneorg_compofolders')


@login_required
def compofolders_show_directory(request, directory_id):
	directory = get_object_or_404(Directory, id=directory_id)
	prefix_len = len(directory.path)

	subdirectories = [d.path[prefix_len:] for d in directory.subdirectories.order_by('path')]
	files = [f.path[prefix_len:] for f in directory.files.order_by('path')]

	return render(request, 'sceneorg/compofolders/show_directory.html', {
		'subdirectories': subdirectories,
		'files': files,
	})


@login_required
def compofolders_show_competition(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)

	placings = competition.placings.prefetch_related('production', 'production__author_nicks', 'production__author_affiliation_nicks')

	return render(request, 'sceneorg/compofolders/show_competition.html', {
		'placings': placings,
	})
