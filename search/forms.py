from django import forms
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.db.models import F, Q

from unidecode import unidecode

from demoscene.models import Releaser
from demoscene.utils.text import generate_search_title
from parties.models import Party
from productions.models import Production, Screenshot


class SearchForm(forms.Form):
	q = forms.CharField(required=True, label='Search')

	def search(self, with_real_names=False, page_number=1, count=50):
		query = self.cleaned_data['q']
		psql_query = SearchQuery(unidecode(query))
		clean_query = generate_search_title(query)
		rank_annotation = SearchRank(F('search_document'), psql_query)

		# Construct the master search query as a union of subqueries that search
		# one model each. Each subquery yields a queryset of dicts with the following fields:
		# 'type': 'production', 'releaser' or 'party'
		# 'pk': primary key of the relevant object
		# 'exactness': magic number used to prioritise exact/prefix title matches in the ordering:
		#     2 = (the cleaned version of) the title exactly matches (the cleaned verson of) the search query
		#     1 = (the cleaned version of) the title starts with (the cleaned version of) the search query
		#     0 = neither of the above
		# 'rank': search ranking as calculated by postgres search

		# start with an empty queryset
		qs = Production.objects.annotate(
			type=models.Value('empty', output_field=models.CharField()),
			exactness=models.Value(0, output_field=models.IntegerField()),
			rank=rank_annotation
		).values('pk', 'type', 'exactness', 'rank').none()

		# Search for productions
		qs = qs.union(
			Production.objects.annotate(
				rank=rank_annotation,
				type=models.Value('production', output_field=models.CharField()),
				exactness=models.Case(
					models.When(search_title=clean_query, then=models.Value(2)),
					models.When(search_title__startswith=clean_query, then=models.Value(1)),
					default=models.Value(0, output_field=models.IntegerField()),
					output_field=models.IntegerField()
				)
			).filter(
				Q(search_document=psql_query)
			).values('pk', 'type', 'exactness', 'rank')
		)

		# Search for releasers
		# TODO: support searching admin-only data (e.g. private real names)
		qs = qs.union(
			Releaser.objects.annotate(
				rank=rank_annotation,
				type=models.Value('releaser', output_field=models.CharField()),
				exactness=models.Case(
					models.When(nicks__variants__search_title=clean_query, then=models.Value(2)),
					models.When(nicks__variants__search_title__startswith=clean_query, then=models.Value(1)),
					default=models.Value(0, output_field=models.IntegerField()),
					output_field=models.IntegerField()
				)
			).filter(
				Q(search_document=psql_query)
			).values('pk', 'type', 'exactness', 'rank')
		)

		# Search for parties
		qs = qs.union(
			Party.objects.annotate(
				rank=rank_annotation,
				type=models.Value('party', output_field=models.CharField()),
				exactness=models.Case(
					models.When(search_title=clean_query, then=models.Value(2)),
					models.When(search_title__startswith=clean_query, then=models.Value(1)),
					default=models.Value(0, output_field=models.IntegerField()),
					output_field=models.IntegerField()
				)
			).filter(
				Q(search_document=psql_query)
			).values('pk', 'type', 'exactness', 'rank'),
		)

		qs = qs.order_by('-exactness', '-rank')

		# Apply pagination to the query before performing the (expensive) real data fetches.

		paginator = Paginator(qs, count)
		# If page request (9999) is out of range, deliver last page of results.
		try:
			page = paginator.page(page_number)
		except (EmptyPage, InvalidPage):
			page = paginator.page(paginator.num_pages)

		# Assemble the results into a plan for fetching the actual models -
		# form a dict that maps model/type to a set of PKs
		to_fetch = {}
		for d in page.object_list:
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
				'group_memberships__group', 'nicks'
			)
			for releaser in releasers:
				fetched[('releaser', releaser.pk)] = releaser

		if 'party' in to_fetch:
			parties = Party.objects.filter(pk__in=to_fetch['party'])
			for party in parties:
				fetched[('party', party.pk)] = party

		# Build final list in same order as returned by the original results query
		results = []
		for d in page.object_list:
			item = fetched.get((d['type'], d['pk'])) or None
			if item:
				item.search_info = d
			results.append(item)

		return (results, page)
