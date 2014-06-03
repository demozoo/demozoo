from django.shortcuts import get_object_or_404
from demoscene.shortcuts import render
from pages.models import Page

def page(request, slug):
	page = get_object_or_404(Page, slug = slug)
	return render(request, 'pages/page.html', {
		'page': page,
	})
