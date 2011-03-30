from search.forms import SearchForm
from django.http import HttpResponseRedirect
from demoscene.shortcuts import render, get_page
from django.contrib import messages

def search(request):
	form = SearchForm(request.GET)
	if form.is_valid():
		query = form.cleaned_data['q']
		results = form.search()
		
		if len(results) == 1:
			messages.success(request, "One match found for '%s'" % query)
			return HttpResponseRedirect(results[0].instance.get_absolute_url())
		page = get_page(results, request.GET.get('page', '1'))
	else:
		query = None
		page = None
	return render(request, 'search/search.html', {
		'form': form,
		'query': query,
		'page': page,
	})
