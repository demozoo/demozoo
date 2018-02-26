from django import forms
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
	for key, model in (
		('production', Production),
		('releaser', Releaser),
		('party', Party),
	):
		ids = to_fetch.get(key) or []
		objects = model.objects.filter(pk__in=ids)

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

	def search(self, with_real_names=False):
		query = unidecode(self.cleaned_data['q'])
		name_results = (name_indexer_with_real_names if with_real_names else name_indexer).search(query).prefetch()
		name_result_ids = set([hit.pk for hit in name_results])

		psql_query = SearchQuery(query)
		rank_annotation = SearchRank(F('search_document'), psql_query)

		# start with an empty queryset
		qs = Production.objects.annotate(
			type=models.Value('empty', output_field=models.CharField()),
			rank=rank_annotation
		).values('pk', 'type', 'rank').none()

		qs = qs.union(
			Production.objects.annotate(
				rank=rank_annotation,
				type=models.Value('production', output_field=models.CharField())
			).filter(
				search_document=query
			).values('pk', 'type', 'rank')
		)
		qs = qs.union(
			Releaser.objects.annotate(
				rank=rank_annotation,
				type=models.Value('releaser', output_field=models.CharField())
			).filter(
				search_document=query
			).values('pk', 'type', 'rank')
		)
		qs = qs.union(
			Party.objects.annotate(
				rank=rank_annotation,
				type=models.Value('party', output_field=models.CharField())
			).filter(
				search_document=query
			).values('pk', 'type', 'rank'),
		)

		qs = qs.order_by('-rank')[:20]
		complete_results = load_mixed_objects(qs)

		# TODO: filter out name results from complete_results
		# TODO: support searching admin-only data (e.g. private real names)
		return (name_results, complete_results, complete_results)
