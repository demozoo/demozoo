from django import forms
from demoscene.index import name_indexer, complete_indexer

class SearchForm(forms.Form):
	q = forms.CharField(required = True, label = 'Search')
	
	def search(self):
		query = self.cleaned_data['q']
		name_results = name_indexer.search(query).prefetch()
		name_result_ids = set([hit.pk for hit in name_results])
		complete_results = complete_indexer.search(query).prefetch()
		# need to filter name_result_ids out from other_results manually,
		# because CompositeIndexer doesn't support filtering:
		# http://code.google.com/p/djapian/issues/detail?id=66
		other_results = []
		for r in complete_results:
			if r.pk not in name_result_ids:
				other_results.append(r)
		return (name_results, other_results, complete_results)
