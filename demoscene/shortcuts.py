from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage

def render(request, template, context={}, **kwargs):
	return render_to_response(template, context, context_instance=RequestContext(request), **kwargs)

# TODO: see if we can (largely) replace this with get_absolute_url
def redirect(*args, **kwargs):
	return HttpResponseRedirect(reverse(*args, **kwargs))

def get_page(queryset, page_number, **kwargs):
	count = kwargs.get('count', 50)
	
	paginator = Paginator(queryset, count)
	
	# Make sure page request is an int. If not, deliver first page.
	try:
		page = int(page_number)
	except ValueError:
		page = 1
	
	# If page request (9999) is out of range, deliver last page of results.
	try:
		return paginator.page(page)
	except (EmptyPage, InvalidPage):
		return paginator.page(paginator.num_pages)
