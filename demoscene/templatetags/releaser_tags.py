from itertools import groupby

from django import template

from productions.models import Screenshot
from tournaments.models import Entry as TournamentEntry


register = template.Library()


# Classes for things that can appear in the credits table, namely
# production credits and tournament participation


class ProductionCredit:
    credit_type = "production"

    def __init__(self, production, nick=None, roles=None, screenshot=None):
        self.production = production
        self.date = production.release_date_date
        self.nick = nick
        self.roles = roles
        self.screenshot = screenshot


class TournamentCredit:
    credit_type = "tournament"

    def __init__(self, tournament, screenshot=None):
        self.tournament = tournament
        self.date = tournament.party.start_date_date
        self.screenshot = screenshot


@register.inclusion_tag("releasers/tags/credited_production_listing.html", takes_context=True)
def combined_releases(context, releaser, include_tournaments=False):
    credits = (
        releaser.credits()
        .select_related("nick")
        .prefetch_related(
            "production__author_nicks__releaser",
            "production__author_affiliation_nicks__releaser",
            "production__platforms",
            "production__types",
        )
        .defer(
            "production__notes",
            "production__author_nicks__releaser__notes",
            "production__author_affiliation_nicks__releaser__notes",
        )
        .order_by("-production__release_date_date", "production__title", "production__id", "nick__name", "nick__id")
    )

    # reorganise credits queryset into a list of
    # (production, nick, [credits_for_that_nick]) records
    credits_by_production = groupby(credits, lambda credit: credit.production)
    # credits_by_production = list of (production, [credits]) records

    credits_by_production_nick = []
    for production, credits in credits_by_production:
        for nick, credits in groupby(credits, lambda credit: credit.nick):
            record = (production, nick, list(credits))
            credits_by_production_nick.append(record)

    # fetch productions by this releaser which are not already covered by credits
    production_ids = [production.id for production, _, _ in credits_by_production_nick]
    productions = (
        releaser.productions()
        .distinct()
        .exclude(id__in=production_ids)
        .prefetch_related("author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types")
        .defer("notes", "author_nicks__releaser__notes", "author_affiliation_nicks__releaser__notes")
        .order_by("-release_date_date", "release_date_precision", "-sortable_title")
    )

    credits_with_prods = credits_by_production_nick + [(prod, None, None) for prod in productions]

    # get final list of production IDs
    production_ids = [production.id for production, _, _ in credits_with_prods]
    # fetch screenshots for those prods
    screenshot_map = Screenshot.select_for_production_ids(production_ids)
    # produce final credits structure for productions
    credits = [
        ProductionCredit(prod, nick, credits, screenshot_map.get(prod.id)) for prod, nick, credits in credits_with_prods
    ]

    if include_tournaments:
        # Add tournament credits
        tournaments = releaser.get_tournament_participations()
        if tournaments:
            tournament_screenshot_map = TournamentEntry.select_screenshots_for_releaser_id(releaser.id)
            credits += [
                TournamentCredit(tournament, tournament_screenshot_map.get(tournament.id)) for tournament in tournaments
            ]

    credits.sort(key=lambda item: (item.date is None, item.date), reverse=True)

    return {
        "releaser": releaser,
        "credits": credits,
        "can_edit": context.get("can_edit", False),
    }


@register.inclusion_tag("releasers/tags/nick_variants.html")
def nick_variants(nick):
    return {
        "differentiator": nick.differentiator,
        "variants": nick.nick_variant_and_abbreviation_list,
    }
