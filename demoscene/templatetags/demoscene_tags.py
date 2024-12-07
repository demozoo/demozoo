from django import template
from django.template.defaultfilters import date as date_format
from django.utils.html import format_html

from bbs.models import BBS
from demoscene.models import Edit, Releaser
from parties.models import Party
from productions.models import Production


register = template.Library()


@register.simple_tag
def field_label(field):
    return format_html('<label for="{0}" class="field_label">{1}</label>', field.id_for_label, field.label)


@register.simple_tag
def date_range(start_date, end_date):
    if start_date.precision != end_date.precision:
        return "%s - %s" % (start_date.explicit_format(), end_date.explicit_format())
    elif start_date.precision == "y":
        if start_date.date.year != end_date.date.year:
            return "%s - %s" % (date_format(start_date.date, arg="Y"), date_format(end_date.date, arg="Y"))
        else:
            return date_format(start_date.date, arg="Y")
    elif start_date.precision == "m":
        if start_date.date.year != end_date.date.year:
            return "%s - %s" % (date_format(start_date.date, arg="F Y"), date_format(end_date.date, arg="F Y"))
        elif start_date.date.month != end_date.date.month:
            return "%s - %s" % (date_format(start_date.date, arg="F"), date_format(end_date.date, arg="F Y"))
        else:
            return date_format(start_date.date, arg="F Y")
    else:
        if start_date.date.year != end_date.date.year:
            return "%s - %s" % (date_format(start_date.date, arg="jS F Y"), date_format(end_date.date, arg="jS F Y"))
        elif start_date.date.month != end_date.date.month:
            return "%s - %s" % (date_format(start_date.date, arg="jS F"), date_format(end_date.date, arg="jS F Y"))
        elif start_date.date.day != end_date.date.day:
            return "%s - %s" % (date_format(start_date.date, arg="jS"), date_format(end_date.date, arg="jS F Y"))
        else:
            return date_format(start_date.date, arg="jS F Y")


@register.inclusion_tag("tags/last_edited_by.html", takes_context=True)
def last_edited_by(context, item):
    edit = Edit.for_model(item, is_admin=context["request"].user.is_staff).order_by("-timestamp").first()
    return {
        "edit": edit,
        "item": item,
    }


@register.simple_tag
def site_stats():
    return {
        "production_count": Production.objects.filter(supertype="production").count(),
        "graphics_count": Production.objects.filter(supertype="graphics").count(),
        "music_count": Production.objects.filter(supertype="music").count(),
        "scener_count": Releaser.objects.filter(is_group=False).count(),
        "group_count": Releaser.objects.filter(is_group=True).count(),
        "party_count": Party.objects.count(),
        "bbs_count": BBS.objects.count(),
    }
