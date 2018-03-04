from django.http import JsonResponse
from django.shortcuts import render

from unidecode import unidecode

from search.forms import SearchForm
from demoscene.index import name_indexer, name_indexer_with_real_names


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
		query = None
		page = None
	return render(request, 'search/search.html', {
		'form': form,
		'query': query,
		'global_search_query': query,
		'results': results,
		'page': page,
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
	return JsonResponse(results, safe=False)
