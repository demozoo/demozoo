from django import template


register = template.Library()


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
