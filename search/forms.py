from __future__ import absolute_import, unicode_literals

import collections
import re

from django import forms
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.db.models import F, Func, Q

from unidecode import unidecode

from demoscene.models import Releaser
from demoscene.utils.text import generate_search_title
from fuzzy_date import FuzzyDate
from parties.models import Party
from platforms.models import Platform
from productions.models import Production, ProductionType, Screenshot


class TSHeadline(Func):
    # Expose the ts_headline function (used for generating search result snippets) to Django ORM.
    function = 'ts_headline'
    output_field = models.TextField()


# match foo:bar, foo:"raster bar" or foo:'copper bar'
FILTER_RE_ONEWORD = re.compile(r'\b(\w+)\:([\w-]+)\b')
FILTER_RE_DOUBLEQUOTE = re.compile(r'\b(\w+)\:\"([^\"]*)\"')
FILTER_RE_SINGLEQUOTE = re.compile(r'\b(\w+)\:\'([^\']*)\'')
TAG_RE = re.compile(r'\[([\w-]+)\]')
RECOGNISED_FILTER_KEYS = ('type', 'platform', 'on', 'by', 'author', 'of', 'group', 'tagged', 'year', 'date', 'before', 'until', 'after', 'since', 'screenshot', 'screenshots')


class SearchForm(forms.Form):
    q = forms.CharField(required=True, label='Search')
    category = forms.ChoiceField(required=False, choices=[
        ('', "Everything"),
        ('production', "Productions"),
        ('graphics', "Graphics"),
        ('music', "Music"),
        ('scener', "Sceners"),
        ('group', "Groups"),
        ('party', "Parties"),
    ])

    def clean(self):
        category = self.cleaned_data.get('category')
        if category and 'q' in self.cleaned_data:
            self.cleaned_data['q'] += (' type:%s' % category)

    def search(self, page_number=1, count=50):
        query = self.cleaned_data['q']

        # Look for filter expressions within query
        filter_expressions = collections.defaultdict(set)
        tag_names = set()

        def apply_filter(match):
            key, val = match.groups()
            if key in RECOGNISED_FILTER_KEYS:
                filter_expressions[key].add(val)
                return ''
            else:
                # the filter has not been recognised;
                # leave the original string intact to be handled as a search term
                return match.group(0)

        for filter_re in (FILTER_RE_ONEWORD, FILTER_RE_SINGLEQUOTE, FILTER_RE_DOUBLEQUOTE):
            query = filter_re.sub(apply_filter, query)

        def apply_tag(match):
            tag_names.add(match.group(1))
            return ''

        query = TAG_RE.sub(apply_tag, query)

        asciified_query = unidecode(query).strip()
        has_search_term = bool(asciified_query)
        if has_search_term:
            psql_query = SearchQuery(unidecode(query))
            clean_query = generate_search_title(query)
            production_filter_q = Q(search_document=psql_query)
            releaser_filter_q = Q(search_document=psql_query)
            party_filter_q = Q(search_document=psql_query)
        else:
            production_filter_q = Q()
            releaser_filter_q = Q()
            party_filter_q = Q()

        subqueries_to_perform = set(['production', 'releaser', 'party'])


        if 'platform' in filter_expressions or 'on' in filter_expressions:
            subqueries_to_perform &= set(['production'])
            platforms = filter_expressions['platform'] | filter_expressions['on']

            platform_ids = Platform.objects.none().values_list('id', flat=True)
            for platform_name in platforms:
                platform_ids |= Platform.objects.filter(Q(name__iexact=platform_name) | Q(aliases__name__iexact=platform_name)).values_list('id', flat=True)

            production_filter_q &= Q(platforms__id__in=list(platform_ids))

        if 'screenshot' in filter_expressions or 'screenshots' in filter_expressions:
            subqueries_to_perform &= set(['production'])

            for flag in filter_expressions['screenshot'] | filter_expressions['screenshots']:
                if flag in ('yes', 'true'):
                    production_filter_q &= Q(has_screenshot=True)
                elif flag in ('no', 'false'):
                    production_filter_q &= Q(has_screenshot=False)

        if 'by' in filter_expressions or 'author' in filter_expressions:
            subqueries_to_perform &= set(['production'])
            for name in filter_expressions['by'] | filter_expressions['author']:
                clean_name = generate_search_title(name)
                production_filter_q &= (
                    # join back through releaser so that we match any nick variant ever used by the author,
                    # not just the nick used on the prod. Better to err on the side of being too liberal
                    Q(author_nicks__releaser__nicks__variants__search_title=clean_name) |
                    Q(author_affiliation_nicks__releaser__nicks__variants__search_title=clean_name)
                )

        if 'of' in filter_expressions:
            subqueries_to_perform &= set(['releaser'])
            for name in filter_expressions['of']:
                clean_name = generate_search_title(name)
                releaser_filter_q &= Q(
                    is_group=False, group_memberships__group__nicks__variants__search_title=clean_name
                )

        if 'group' in filter_expressions:
            subqueries_to_perform &= set(['production', 'releaser'])
            for name in filter_expressions['group']:
                clean_name = generate_search_title(name)
                releaser_filter_q &= Q(
                    is_group=False, group_memberships__group__nicks__variants__search_title=clean_name
                )
                production_filter_q &= (
                    # join back through releaser so that we match any nick variant ever used by the author,
                    # not just the nick used on the prod. Better to err on the side of being too liberal
                    Q(
                        author_nicks__releaser__is_group=True,
                        author_nicks__releaser__nicks__variants__search_title=clean_name
                    ) | Q(
                        author_affiliation_nicks__releaser__nicks__variants__search_title=clean_name
                    )
                )

        if tag_names or ('tagged' in filter_expressions):
            subqueries_to_perform &= set(['production'])
            for tag_name in filter_expressions['tagged'] | tag_names:
                production_filter_q &= Q(tags__name=tag_name)

        if 'year' in filter_expressions or 'date' in filter_expressions:
            subqueries_to_perform &= set(['production', 'party'])
            for date_str in filter_expressions['year'] | filter_expressions['date']:
                try:
                    date_expr = FuzzyDate.parse(date_str)
                except ValueError:
                    continue

                production_filter_q &= Q(release_date_date__gte=date_expr.date_range_start(), release_date_date__lte=date_expr.date_range_end())
                party_filter_q &= Q(end_date_date__gte=date_expr.date_range_start(), start_date_date__lte=date_expr.date_range_end())

        if 'before' in filter_expressions:
            subqueries_to_perform &= set(['production', 'party'])
            for date_str in filter_expressions['before']:
                try:
                    date_expr = FuzzyDate.parse(date_str)
                except ValueError:
                    continue

                production_filter_q &= Q(release_date_date__lt=date_expr.date_range_start())
                party_filter_q &= Q(start_date_date__lt=date_expr.date_range_start())

        if 'until' in filter_expressions:
            subqueries_to_perform &= set(['production', 'party'])
            for date_str in filter_expressions['until']:
                try:
                    date_expr = FuzzyDate.parse(date_str)
                except ValueError:
                    continue

                production_filter_q &= Q(release_date_date__lte=date_expr.date_range_end())
                party_filter_q &= Q(start_date_date__lte=date_expr.date_range_end())

        if 'after' in filter_expressions:
            subqueries_to_perform &= set(['production', 'party'])
            for date_str in filter_expressions['after']:
                try:
                    date_expr = FuzzyDate.parse(date_str)
                except ValueError:
                    continue

                production_filter_q &= Q(release_date_date__gt=date_expr.date_range_end())
                party_filter_q &= Q(end_date_date__gt=date_expr.date_range_end())

        if 'since' in filter_expressions:
            subqueries_to_perform &= set(['production', 'party'])
            for date_str in filter_expressions['since']:
                try:
                    date_expr = FuzzyDate.parse(date_str)
                except ValueError:
                    continue

                production_filter_q &= Q(release_date_date__gte=date_expr.date_range_start())
                party_filter_q &= Q(end_date_date__gte=date_expr.date_range_start())

        if 'type' in filter_expressions:
            requested_types = filter_expressions['type']
            subqueries_from_type = set()
            filter_by_prod_supertype = False
            production_supertypes = []

            for supertype in ('production', 'graphics', 'music'):
                if supertype in requested_types:
                    filter_by_prod_supertype = True
                    production_supertypes.append(supertype)

            if filter_by_prod_supertype:
                subqueries_from_type.add('production')
                production_filter_q &= Q(supertype__in=production_supertypes)

            if 'releaser' in requested_types or 'scener' in requested_types or 'group' in requested_types:
                subqueries_from_type.add('releaser')

                if 'scener' in requested_types and not ('releaser' in requested_types or 'group' in requested_types):
                    releaser_filter_q &= Q(is_group=False)

                if 'group' in requested_types and not ('releaser' in requested_types or 'scener' in requested_types):
                    releaser_filter_q &= Q(is_group=True)

            if 'party' in requested_types:
                subqueries_from_type.add('party')

            # assume that any otherwise-unrecognised 'type' values indicate a production type
            production_types = set()
            for val in requested_types:
                if val not in ('production', 'graphics', 'music', 'scener', 'group', 'releaser', 'party'):
                    production_types.add(val)

            if production_types:
                prod_type_names_q = Q()
                for name in production_types:
                    prod_type_names_q |= Q(name__iexact=name)
                prod_type_ids = ProductionType.objects.filter(prod_type_names_q).values_list('id', flat=True)

                subqueries_from_type.add('production')
                production_filter_q &= Q(types__in=prod_type_ids)

            subqueries_to_perform &= subqueries_from_type

        # Construct the master search query as a union of subqueries that search
        # one model each. Each subquery yields a queryset of dicts with the following fields:
        # 'type': 'production', 'releaser' or 'party'
        # 'pk': primary key of the relevant object
        # 'exactness': magic number used to prioritise exact/prefix title matches in the ordering:
        #     2 = (the cleaned version of) the title exactly matches (the cleaned verson of) the search query
        #     1 = (the cleaned version of) the title starts with (the cleaned version of) the search query
        #     0 = neither of the above
        # 'rank': search ranking as calculated by postgres search

        # start with an empty queryset
        if has_search_term:
            rank_annotation = SearchRank(F('search_document'), psql_query)
        else:
            rank_annotation = models.Value('', output_field=models.CharField())

        qs = Production.objects.annotate(
            type=models.Value('empty', output_field=models.CharField()),
            exactness=models.Value(0, output_field=models.IntegerField()),
            rank=rank_annotation
        ).values('pk', 'type', 'exactness', 'rank').none()

        if 'production' in subqueries_to_perform:
            # Search for productions

            if has_search_term:
                rank_annotation = SearchRank(F('search_document'), psql_query)
                exactness_annotation = models.Case(
                    models.When(search_title=clean_query, then=models.Value(2)),
                    models.When(search_title__startswith=clean_query, then=models.Value(1)),
                    default=models.Value(0, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                )
            else:
                rank_annotation = F('sortable_title')
                exactness_annotation = models.Value(0, output_field=models.IntegerField())

            qs = qs.union(
                Production.objects.annotate(
                    rank=rank_annotation,
                    type=models.Value('production', output_field=models.CharField()),
                    exactness=exactness_annotation
                ).filter(
                    production_filter_q
                ).order_by(
                    # empty order_by to cancel the Production model's native ordering
                ).distinct().values('pk', 'type', 'exactness', 'rank')
            )

        if 'releaser' in subqueries_to_perform:
            # Search for releasers

            if has_search_term:
                rank_annotation = SearchRank(F('search_document'), psql_query)
                # Exactness test will be applied to each of the releaser's nick variants;
                # take the highest result
                exactness_annotation = models.Max(models.Case(
                    models.When(nicks__variants__search_title=clean_query, then=models.Value(2)),
                    models.When(nicks__variants__search_title__startswith=clean_query, then=models.Value(1)),
                    default=models.Value(0, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ))
            else:
                rank_annotation = F('name')
                exactness_annotation = models.Value(0, output_field=models.IntegerField())

            qs = qs.union(
                Releaser.objects.annotate(
                    rank=rank_annotation,
                    type=models.Value('releaser', output_field=models.CharField()),
                    exactness=exactness_annotation
                ).filter(
                    releaser_filter_q
                ).distinct().order_by(
                    # empty order_by to cancel the Releaser model's native ordering
                ).values('pk', 'type', 'exactness', 'rank')
            )

        if 'party' in subqueries_to_perform:
            # Search for parties

            if has_search_term:
                rank_annotation = SearchRank(F('search_document'), psql_query)
                exactness_annotation = models.Case(
                    models.When(search_title=clean_query, then=models.Value(2)),
                    models.When(search_title__startswith=clean_query, then=models.Value(1)),
                    default=models.Value(0, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                )
            else:
                rank_annotation = F('name')
                exactness_annotation = models.Value(0, output_field=models.IntegerField())

            qs = qs.union(
                Party.objects.annotate(
                    rank=rank_annotation,
                    type=models.Value('party', output_field=models.CharField()),
                    exactness=exactness_annotation,
                ).filter(
                    party_filter_q
                ).order_by(
                    # empty order_by to cancel the Party model's native ordering
                ).values('pk', 'type', 'exactness', 'rank'),
            )

        if has_search_term:
            qs = qs.order_by('-exactness', '-rank', 'pk')
        else:
            qs = qs.order_by('-exactness', 'rank', 'pk')

        # Apply pagination to the query before performing the (expensive) real data fetches.

        paginator = Paginator(qs, count)
        # If page request (9999) is out of range, deliver last page of results.
        try:
            page = paginator.page(page_number)
        except (EmptyPage, InvalidPage):
            page = paginator.page(paginator.num_pages)

        # Assemble the results into a plan for fetching the actual models -
        # form a dict that maps model/type to a set of PKs
        to_fetch = {}
        for d in page.object_list:
            to_fetch.setdefault(d['type'], set()).add(d['pk'])

        # now do the fetches, and store the results as a mapping of (type, pk) tuple to object
        fetched = {}

        if 'production' in to_fetch:
            production_ids = to_fetch['production']
            productions = Production.objects.filter(pk__in=production_ids).prefetch_related(
                'author_nicks__releaser', 'author_affiliation_nicks__releaser'
            )
            if has_search_term:
                productions = productions.annotate(
                    search_snippet=TSHeadline('notes', psql_query)
                )
            screenshots = Screenshot.select_for_production_ids(production_ids)

            for prod in productions:
                prod.selected_screenshot = screenshots.get(prod.pk)
                # Ignore any search snippets that don't actually contain a highlighted term
                prod.has_search_snippet = has_search_term and '<b>' in prod.search_snippet
                fetched[('production', prod.pk)] = prod

        if 'releaser' in to_fetch:
            releasers = Releaser.objects.filter(pk__in=to_fetch['releaser']).prefetch_related(
                'group_memberships__group__nicks', 'nicks'
            )
            if has_search_term:
                releasers = releasers.annotate(
                    search_snippet=TSHeadline('notes', psql_query)
                )
            for releaser in releasers:
                releaser.has_search_snippet = has_search_term and '<b>' in releaser.search_snippet
                fetched[('releaser', releaser.pk)] = releaser

        if 'party' in to_fetch:
            parties = Party.objects.filter(pk__in=to_fetch['party'])
            if has_search_term:
                parties = parties.annotate(
                    search_snippet=TSHeadline('notes', psql_query)
                )
            for party in parties:
                party.has_search_snippet = has_search_term and '<b>' in party.search_snippet
                fetched[('party', party.pk)] = party

        # Build final list in same order as returned by the original results query
        results = []
        for d in page.object_list:
            item = fetched.get((d['type'], d['pk'])) or None
            if item:
                item.search_info = d
                results.append(item)

        return (results, page)
