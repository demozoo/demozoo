from django import forms
from demoscene.index import complete_indexer

class SearchForm(forms.Form):
	q = forms.CharField(required = True, label = 'Search')
	
	def search(self):
		query = self.cleaned_data['q']
		return complete_indexer.search(query).prefetch()
