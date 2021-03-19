from __future__ import absolute_import, unicode_literals

from django.shortcuts import get_object_or_404, render

from pages.models import Page


def page(request, slug):
    page = get_object_or_404(Page, slug = slug)
    return render(request, 'pages/page.html', {
        'page': page,
    })
