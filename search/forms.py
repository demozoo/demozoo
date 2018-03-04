from django import forms
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.db.models import F

from unidecode import unidecode

from demoscene.index import name_indexer, name_indexer_with_real_names
from demoscene.models import Releaser
from parties.models import Party
from productions.models import Production


def load_mixed_objects(dicts):
	"""
	Takes a list of dictionaries, each of which must at least have a 'type'
	and a 'pk' key. Returns a list of ORM objects of those various types.
	Each returned ORM object has a .original_dict attribute populated.
	"""
	to_fetch = {}
	for d in dicts:
		to_fetch.setdefault(d['type'], set()).add(d['pk'])
	fetched = {}
	for key, model, prefetch_fields in (
		('production', Production, ['author_nicks__releaser', 'author_affiliation_nicks__releaser']),
		('releaser', Releaser, ['group_memberships__group']),
		('party', Party, []),
	):
		ids = to_fetch.get(key) or []
		objects = model.objects.filter(pk__in=ids)
		if prefetch_fields:
			objects = objects.prefetch_related(*prefetch_fields)

		for obj in objects:
			fetched[(key, obj.pk)] = obj
	# Build list in same order as dicts argument
	to_return = []
	for d in dicts:
		item = fetched.get((d['type'], d['pk'])) or None
		if item:
			item.original_dict = d
		to_return.append(item)
	return to_return


class SearchForm(forms.Form):
	q = forms.CharField(required=True, label='Search')

	def search(self, with_real_names=False, page_number=1, count=50):
		query = unidecode(self.cleaned_data['q'])
		psql_query = SearchQuery(query)
		rank_annotation = SearchRank(F('search_document'), psql_query)

		# start with an empty queryset
		qs = Production.objects.annotate(
			type=models.Value('empty', output_field=models.CharField()),
			sort_title=F('title'),
			rank=rank_annotation
		).values('pk', 'sort_title', 'type', 'rank').none()

		qs = qs.union(
			Production.objects.annotate(
				rank=rank_annotation,
				type=models.Value('production', output_field=models.CharField()),
				sort_title=F('sortable_title'),
			).filter(
				search_document=query
			).values('pk', 'sort_title', 'type', 'rank')
		)
		qs = qs.union(
			Releaser.objects.annotate(
				rank=rank_annotation,
				type=models.Value('releaser', output_field=models.CharField()),
				sort_title=F('name'),
			).filter(
				search_document=query
			).values('pk', 'sort_title', 'type', 'rank')
		)
		qs = qs.union(
			Party.objects.annotate(
				rank=rank_annotation,
				type=models.Value('party', output_field=models.CharField()),
				sort_title=F('name'),
			).filter(
				search_document=query
			).values('pk', 'sort_title', 'type', 'rank'),
		)

		qs = qs.order_by('-rank', 'sort_title')

		paginator = Paginator(qs, count)
		# If page request (9999) is out of range, deliver last page of results.
		try:
			page = paginator.page(page_number)
		except (EmptyPage, InvalidPage):
			page = paginator.page(paginator.num_pages)

		results = load_mixed_objects(page.object_list)

		# TODO: separate section for exact name matches
		# TODO: support searching admin-only data (e.g. private real names)
		return (results, page)
