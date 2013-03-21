from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils import simplejson

from search.forms import SearchForm
from demoscene.shortcuts import render, get_page
from demoscene.index import name_indexer

def search(request):
	form = SearchForm(request.GET)
	if form.is_valid():
		query = form.cleaned_data['q']
		(name_results, results, resultset) = form.search()
		
		if len(name_results) == 1 and len(results) == 0:
			messages.success(request, "One match found for '%s'" % query)
			return HttpResponseRedirect(name_results[0].instance.get_absolute_url())
		page = get_page(results, request.GET.get('page', '1'))
	else:
		query = None
		page = None
		name_results = None
		resultset = None
	return render(request, 'search/search.html', {
		'form': form,
		'query': query,
		'name_results': name_results,
		'page': page,
		'resultset': resultset,
	})

def live_search(request):
	query = request.GET.get('q')
	if query:
		results = name_indexer.search(query).flags(name_indexer.flags.PARTIAL)[0:10].prefetch()
		results = [hit.instance.search_result_json() for hit in results]
	else:
		results = []

	return HttpResponse(simplejson.dumps(results), mimetype="text/javascript")
