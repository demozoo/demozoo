import collections
import re

from django import forms
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.db.models import F, Func, Q

from unidecode import unidecode

from demoscene.models import Releaser
from demoscene.utils.text import generate_search_title
from parties.models import Party
from productions.models import Production, Screenshot


class TSHeadline(Func):
	# Expose the ts_headline function (used for generating search result snippets) to Django ORM.
	function = 'ts_headline'
	output_field = models.TextField()


# match foo:bar, foo:"raster bar" or foo:'copper bar'
FILTER_RE_ONEWORD = re.compile(r'\b(\w+)\:(\w+)\b')
FILTER_RE_DOUBLEQUOTE = re.compile(r'\b(\w+)\:\"([^\"]*)\"')
FILTER_RE_SINGLEQUOTE = re.compile(r'\b(\w+)\:\'([^\']*)\'')
RECOGNISED_FILTER_KEYS = ('type', 'platform', 'on', 'by', 'author')


class SearchForm(forms.Form):
	q = forms.CharField(required=True, label='Search')

	def search(self, with_real_names=False, page_number=1, count=50):
		query = self.cleaned_data['q']

		# Look for filter expressions within query
		filter_expressions = collections.defaultdict(set)

		def apply_filter(match):
			key, val = match.groups()
			if key in RECOGNISED_FILTER_KEYS:
				filter_expressions[key].add(val)
				return ''
			else:
				# the filter has not been recognised;
				# leave the original string intact to be handled as a search term
				return match.group(0)

		for filter_re in (FILTER_RE_ONEWORD, FILTER_RE_SINGLEQUOTE, FILTER_RE_DOUBLEQUOTE):
			query = filter_re.sub(apply_filter, query)

		psql_query = SearchQuery(unidecode(query))
		clean_query = generate_search_title(query)
		rank_annotation = SearchRank(F('search_document'), psql_query)

		subqueries_to_perform = set(['production', 'releaser', 'party'])

		production_filter_q = Q(search_document=psql_query)

		if with_real_names:
			releaser_filter_q = Q(admin_search_document=psql_query)
			releaser_rank_annotation = SearchRank(F('admin_search_document'), psql_query)
		else:
			releaser_filter_q = Q(search_document=psql_query)
			releaser_rank_annotation = rank_annotation

		party_filter_q = Q(search_document=psql_query)

		if 'platform' in filter_expressions or 'on' in filter_expressions:
			subqueries_to_perform &= set(['production'])
			platforms = filter_expressions['platform'] | filter_expressions['on']
			production_filter_q &= Q(platforms__name__in=platforms)

		if 'by' in filter_expressions or 'author' in filter_expressions:
			subqueries_to_perform &= set(['production'])
			for name in filter_expressions['by'] | filter_expressions['author']:
				clean_name = generate_search_title(name)
				production_filter_q &= (
					Q(author_nicks__variants__search_title=clean_name) |
					Q(author_affiliation_nicks__variants__search_title=clean_name)
				)

		if 'type' in filter_expressions:
			requested_types = filter_expressions['type']
			subqueries_from_type = set()
			filter_by_prod_supertype = False
			production_supertypes = []

			for supertype in ('production', 'graphics', 'music'):
				if supertype in requested_types:
					filter_by_prod_supertype = True
					production_supertypes.append(supertype)

			if filter_by_prod_supertype:
				subqueries_from_type.add('production')
				production_filter_q &= Q(supertype__in=production_supertypes)

			if 'releaser' in requested_types or 'scener' in requested_types or 'group' in requested_types:
				subqueries_from_type.add('releaser')

				if 'scener' in requested_types and not ('releaser' in requested_types or 'group' in requested_types):
					releaser_filter_q &= Q(is_group=False)

				if 'group' in requested_types and not ('releaser' in requested_types or 'scener' in requested_types):
					releaser_filter_q &= Q(is_group=True)

			if 'party' in requested_types:
				subqueries_from_type.add('party')

			# assume that any otherwise-unrecognised 'type' values indicate a production type
			production_types = set()
			for val in requested_types:
				if val not in ('production', 'graphics', 'music', 'scener', 'group', 'releaser', 'party'):
					production_types.add(val)

			if production_types:
				subqueries_from_type.add('production')
				production_filter_q &= Q(types__name__in=production_types)

			subqueries_to_perform &= subqueries_from_type

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

		if 'production' in subqueries_to_perform:
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
					production_filter_q
				).order_by(
					# empty order_by to cancel the Production model's native ordering
				).distinct().values('pk', 'type', 'exactness', 'rank')
			)

		if 'releaser' in subqueries_to_perform:
			# Search for releasers
			qs = qs.union(
				Releaser.objects.annotate(
					rank=releaser_rank_annotation,
					type=models.Value('releaser', output_field=models.CharField()),
					# Exactness test will be applied to each of the releaser's nick variants;
					# take the highest result
					exactness=models.Max(models.Case(
						models.When(nicks__variants__search_title=clean_query, then=models.Value(2)),
						models.When(nicks__variants__search_title__startswith=clean_query, then=models.Value(1)),
						default=models.Value(0, output_field=models.IntegerField()),
						output_field=models.IntegerField()
					))
				).filter(
					releaser_filter_q
				).order_by(
					# empty order_by to cancel the Releaser model's native ordering
				).values('pk', 'type', 'exactness', 'rank')
			)

		if 'party' in subqueries_to_perform:
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
					party_filter_q
				).order_by(
					# empty order_by to cancel the Party model's native ordering
				).values('pk', 'type', 'exactness', 'rank'),
			)

		qs = qs.order_by('-exactness', '-rank', 'pk')

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
			).annotate(
				search_snippet=TSHeadline('notes', psql_query)
			)
			screenshots = Screenshot.select_for_production_ids(production_ids)

			for prod in productions:
				prod.selected_screenshot = screenshots.get(prod.pk)
				# Ignore any search snippets that don't actually contain a highlighted term
				prod.has_search_snippet = '<b>' in prod.search_snippet
				fetched[('production', prod.pk)] = prod

		if 'releaser' in to_fetch:
			releasers = Releaser.objects.filter(pk__in=to_fetch['releaser']).prefetch_related(
				'group_memberships__group__nicks', 'nicks'
			).annotate(
				search_snippet=TSHeadline('notes', psql_query)
			)
			for releaser in releasers:
				releaser.has_search_snippet = '<b>' in releaser.search_snippet
				fetched[('releaser', releaser.pk)] = releaser

		if 'party' in to_fetch:
			parties = Party.objects.filter(pk__in=to_fetch['party']).annotate(
				search_snippet=TSHeadline('notes', psql_query)
			)
			for party in parties:
				party.has_search_snippet = '<b>' in party.search_snippet
				fetched[('party', party.pk)] = party

		# Build final list in same order as returned by the original results query
		results = []
		for d in page.object_list:
			item = fetched.get((d['type'], d['pk'])) or None
			if item:
				item.search_info = d
			results.append(item)

		return (results, page)
