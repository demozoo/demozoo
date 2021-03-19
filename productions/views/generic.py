from django.shortcuts import render
from django.views import View

from demoscene.shortcuts import get_page
from productions.models import Production, ProductionType


class IndexView(View):
    # subclasses provide supertype, filter_form_class, template

    def get(self, request):
        queryset = Production.objects.filter(supertype=self.supertype)

        order = request.GET.get('order', 'date')
        asc = request.GET.get('dir', 'desc') == 'asc'

        queryset = apply_order(queryset, order, asc)

        form = self.filter_form_class(request.GET)

        if form.is_valid():
            if form.cleaned_data['platform']:
                queryset = queryset.filter(platforms=form.cleaned_data['platform'])
            if form.cleaned_data['production_type']:
                prod_types = ProductionType.get_tree(form.cleaned_data['production_type'])
                queryset = queryset.filter(types__in=prod_types)

        queryset = queryset.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')

        production_page = get_page(
            queryset,
            request.GET.get('page', '1'))

        return render(request, self.template, {
            'order': order,
            'production_page': production_page,
            'menu_section': "productions",
            'asc': asc,
            'form': form,
        })


def apply_order(queryset, order, asc):
    if order == 'title':
        return queryset.order_by('%ssortable_title' % ('' if asc else '-'))
    else:  # date
        if asc:
            return queryset.order_by('release_date_date', 'title')
        else:
            # fiddle order so that empty release dates end up at the end
            return queryset.extra(
                select={'order_date': "coalesce(productions_production.release_date_date, '1970-01-01')"}
            ).order_by('-order_date', '-title')
