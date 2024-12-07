from django import template
from django.conf import settings

from productions.models import Screenshot


register = template.Library()


@register.inclusion_tag("productions/tags/byline.html")
def byline(production):
    return {
        "unparsed_byline": production.unparsed_byline,
        "authors": [(nick, nick.releaser) for nick in production.author_nicks_with_authors()],
        "affiliations": [(nick, nick.releaser) for nick in production.author_affiliation_nicks_with_groups()],
    }


@register.inclusion_tag("productions/tags/core_details.html", takes_context=True)
def production_core_details(context, production, subpage=False):
    ctx = {
        "production": production,
        "invitation_parties": production.invitation_parties.order_by("start_date_date"),
        "bbses_advertised": production.bbses.order_by("name"),
        "release_parties": production.release_parties.order_by("start_date_date"),
        "competition_placings": (
            production.competition_placings.select_related("competition__party").order_by(
                "competition__party__start_date_date"
            )
        ),
    }
    if subpage:
        ctx.update(
            {
                "show_back_button": True,
            }
        )
    else:
        is_staff = context["request"].user.is_staff
        ctx.update(
            {
                "show_edit_button": context["site_is_writeable"] and (is_staff or not production.locked),
                "show_locked_button": context["request"].user.is_authenticated and production.locked,
                "show_lock_button": is_staff and context["site_is_writeable"] and not production.locked,
                "show_back_button": False,
            }
        )

    return ctx


@register.inclusion_tag("productions/tags/production_listing.html")
def production_listing(productions, show_screenshots=False, show_prod_types=False, mark_excludable=False):
    if show_screenshots:
        screenshots = Screenshot.select_for_production_ids([prod.id for prod in productions])
    else:
        screenshots = {}

    productions_and_screenshots = [(production, screenshots.get(production.id)) for production in productions]
    return {
        "productions_and_screenshots": productions_and_screenshots,
        "show_screenshots": show_screenshots,
        "show_prod_types": show_prod_types,
        "mark_excludable": mark_excludable,
        "site_is_writeable": settings.SITE_IS_WRITEABLE,
    }
