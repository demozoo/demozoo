from django.db import models
from django.http import JsonResponse
from django.shortcuts import render


from search.forms import SearchForm
from demoscene.models import Releaser
from demoscene.utils.text import generate_search_title
from parties.models import Party
from productions.models import Production, Screenshot


def search(request):
	form = SearchForm(request.GET)
	if form.is_valid():
		query = form.cleaned_data['q']

		has_real_name_access = request.user.has_perm('demoscene.view_releaser_real_names')

		page_number = request.GET.get('page', '1')
		# Make sure page request is an int. If not, deliver first page.
		try:
			page_number = int(page_number)
		except ValueError:
			page_number = 1

		results, page = form.search(with_real_names=has_real_name_access, page_number=page_number)
	else:
		query = ''
		page = None
		results = None
	return render(request, 'search/search.html', {
		'form': form,
		'query': query,
		'results': results,
		'page': page,
	})


def live_search(request):
	query = request.GET.get('q')
	if query:
		clean_query = generate_search_title(query)

		# start with an empty queryset
		qs = Production.objects.annotate(
			type=models.Value('empty', output_field=models.CharField()),
		).values('pk', 'type').none()
		qs = qs.union(
			Production.objects.annotate(
				type=models.Value('production', output_field=models.CharField()),
			).filter(search_title__startswith=clean_query).values('pk', 'type')
		)
		qs = qs.union(
			Releaser.objects.annotate(
				type=models.Value('releaser', output_field=models.CharField()),
			).filter(nicks__variants__search_title__startswith=clean_query).values('pk', 'type')
		)
		qs = qs.union(
			Party.objects.annotate(
				type=models.Value('party', output_field=models.CharField()),
			).filter(search_title__startswith=clean_query).values('pk', 'type')
		)
		search_result_data = list(qs[:10])

		# Assemble the results into a plan for fetching the actual models -
		# form a dict that maps model/type to a set of PKs
		to_fetch = {}
		for d in search_result_data:
			to_fetch.setdefault(d['type'], set()).add(d['pk'])

		# now do the fetches, and store the results as a mapping of (type, pk) tuple to object
		fetched = {}

		if 'production' in to_fetch:
			production_ids = to_fetch['production']
			productions = Production.objects.filter(pk__in=production_ids).prefetch_related(
				'author_nicks__releaser', 'author_affiliation_nicks__releaser'
			)
			screenshots = Screenshot.select_for_production_ids(production_ids)

			for prod in productions:
				prod.selected_screenshot = screenshots.get(prod.pk)
				fetched[('production', prod.pk)] = prod

		if 'releaser' in to_fetch:
			releasers = Releaser.objects.filter(pk__in=to_fetch['releaser']).prefetch_related(
				'group_memberships__group__nicks', 'nicks'
			)
			for releaser in releasers:
				fetched[('releaser', releaser.pk)] = releaser

		if 'party' in to_fetch:
			parties = Party.objects.filter(pk__in=to_fetch['party'])
			for party in parties:
				fetched[('party', party.pk)] = party

		# Build final list in same order as returned by the original results query
		results = []
		for d in search_result_data:
			item = fetched.get((d['type'], d['pk'])) or None
			if item:
				if d['type'] == 'production':
					if item.selected_screenshot:
						screenshot = item.selected_screenshot
						width, height = screenshot.thumb_dimensions_to_fit(48, 36)
						thumbnail = {
							'url': screenshot.thumbnail_url,
							'width': width, 'height': height,
							'natural_width': screenshot.thumbnail_width,
							'natural_height': screenshot.thumbnail_height,
						}
					else:
						thumbnail = None

					results.append({
						'type': item.supertype,
						'url': item.get_absolute_url(),
						'value': item.title_with_byline,
						'thumbnail': thumbnail
					})
				elif d['type'] == 'releaser':
					primary_nick = item.primary_nick
					if primary_nick.differentiator:
						differentiator = " (%s)" % primary_nick.differentiator
					else:
						differentiator = ""

					results.append({
						'type': 'group' if item.is_group else 'scener',
						'url': item.get_absolute_url(),
						'value': item.name_with_affiliations() + differentiator,
					})
				elif d['type'] == 'party':
					results.append({
						'type': 'party',
						'url': item.get_absolute_url(),
						'value': item.name,
					})

	else:
		results = []
	return JsonResponse(results, safe=False)
