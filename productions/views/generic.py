import random

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import View

from awards.models import Event
from comments.forms import CommentForm
from comments.models import Comment
from demoscene.shortcuts import get_page
from productions.carousel import Carousel
from productions.forms import ProductionTagsForm
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

        queryset = queryset.prefetch_related(
            'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types'
        )

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


class ShowView(View):
    supertype = 'production'

    def get(self, request, production_id, edit_mode=False):
        self.production = get_object_or_404(Production, id=production_id)
        if self.production.supertype != self.supertype:
            return HttpResponseRedirect(self.production.get_absolute_url())

        return render(self.request, 'productions/show.html', self.get_context_data())

    def get_context_data(self):
        if self.request.user.is_authenticated:
            comment = Comment(commentable=self.production, user=self.request.user)
            comment_form = CommentForm(instance=comment, prefix="comment")
            tags_form = ProductionTagsForm(instance=self.production)

            awards_accepting_recommendations = [
                (event, event.get_recommendation_options(self.request.user, self.production))
                for event in Event.accepting_recommendations_for(self.production)
            ]
        else:
            comment_form = None
            tags_form = None

            awards_accepting_recommendations = [
                (event, None)
                for event in Event.accepting_recommendations_for(self.production)
            ]

        if self.production.can_have_pack_members():
            pack_members = [
                link.member for link in
                (
                    self.production.pack_members.select_related('member')
                    .prefetch_related('member__author_nicks__releaser', 'member__author_affiliation_nicks__releaser')
                )
            ]
        else:
            pack_members = None

        try:
            meta_screenshot = random.choice(self.production.screenshots.exclude(standard_url=''))
        except IndexError:
            meta_screenshot = None

        return {
            'production': self.production,
            'prompt_to_edit': settings.SITE_IS_WRITEABLE and (self.request.user.is_staff or not self.production.locked),
            'download_links': self.production.download_links,
            'external_links': self.production.external_links,
            'info_files': self.production.info_files.all(),
            'editing_credits': (self.request.GET.get('editing') == 'credits'),
            'credits': self.production.credits_for_listing(),
            'carousel': Carousel(self.production, self.request.user),

            'tags': self.production.tags.order_by('name'),
            'blurbs': self.production.blurbs.all() if self.request.user.is_staff else None,
            'comment_form': comment_form,
            'tags_form': tags_form,
            'meta_screenshot': meta_screenshot,
            'awards_accepting_recommendations': awards_accepting_recommendations,
            'pack_members': pack_members,
        }
