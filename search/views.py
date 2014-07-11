from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils import simplejson
from django.shortcuts import render

from unidecode import unidecode

from search.forms import SearchForm
from demoscene.shortcuts import get_page
from demoscene.index import name_indexer, name_indexer_with_real_names

def search(request):
	form = SearchForm(request.GET)
	if form.is_valid():
		query = form.cleaned_data['q']

		has_real_name_access = request.user.has_perm('demoscene.view_releaser_real_names')
		(name_results, results, resultset) = form.search(with_real_names=has_real_name_access)
		
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
		query = unidecode(query)
		has_real_name_access = request.user.has_perm('demoscene.view_releaser_real_names')
		results = (name_indexer_with_real_names if has_real_name_access else name_indexer).search(query).flags(name_indexer.flags.PARTIAL)[0:10].prefetch()
		results = [hit.instance.search_result_json() for hit in results]
	else:
		results = []

	return HttpResponse(simplejson.dumps(results), mimetype="text/javascript")
