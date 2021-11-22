from itertools import groupby

from django import template

from productions.models import Screenshot


register = template.Library()


@register.inclusion_tag('shared/credited_production_listing.html')
def combined_releases(releaser):

    credits = (
        releaser.credits().select_related('nick')
        .prefetch_related(
            'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser',
            'production__platforms', 'production__types'
        )
        .defer(
            'production__notes', 'production__author_nicks__releaser__notes',
            'production__author_affiliation_nicks__releaser__notes'
        )
        .order_by(
            '-production__release_date_date', 'production__title', 'production__id', 'nick__name', 'nick__id'
        )
    )

    # reorganise credits queryset into a list of
    # (production, nick, [credits_for_that_nick]) records
    credits_by_production = groupby(credits, lambda credit: credit.production)
    # credits_by_production = list of (production, [credits]) records

    credits_by_production_nick = []
    for (production, credits) in credits_by_production:
        for (nick, credits) in groupby(credits, lambda credit: credit.nick):
            record = (production, nick, list(credits))
            credits_by_production_nick.append(record)

    # fetch productions by this releaser which are not already covered by credits
    production_ids = [production.id for production, _, _ in credits_by_production_nick]
    productions = releaser.productions().distinct()\
        .exclude(id__in=production_ids)\
        .prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')\
        .defer('notes', 'author_nicks__releaser__notes', 'author_affiliation_nicks__releaser__notes')\
        .order_by('-release_date_date', 'release_date_precision', '-sortable_title')

    credits_with_prods = credits_by_production_nick + [(prod, None, None) for prod in productions]
    credits_with_prods.sort(
        key=lambda item: (item[0].release_date_date is None, item[0].release_date_date),
        reverse=True
    )

    # get final list of production IDs
    production_ids = [production.id for production, _, _ in credits_with_prods]
    # fetch screenshots for those prods
    screenshot_map = Screenshot.select_for_production_ids(production_ids)
    # produce final credits struct: (production, nick, [credits], screenshot)
    credits_with_prods_and_screenshots = [
        (prod, nick, credits, screenshot_map.get(prod.id))
        for prod, nick, credits in credits_with_prods
    ]

    return {
        'releaser': releaser,
        'credits': credits_with_prods_and_screenshots,
    }
