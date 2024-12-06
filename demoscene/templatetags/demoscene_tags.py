from django import template
from django.conf import settings
from django.template.defaultfilters import date as date_format
from django.utils.html import format_html

from bbs.models import BBS
from demoscene.models import Edit, Nick, Releaser
from parties.models import Party
from productions.models import Production, Screenshot


register = template.Library()


@register.inclusion_tag('tags/nick_variants.html')
def nick_variants(nick):
    return {
        'differentiator': nick.differentiator,
        'variants': nick.nick_variant_and_abbreviation_list,
    }


@register.inclusion_tag('tags/scener_with_affiliations.html')
def scener_with_affiliations(releaser_or_nick):
    if isinstance(releaser_or_nick, Nick):
        releaser = releaser_or_nick.releaser
    else:  # assume a Releaser
        releaser = releaser_or_nick
    groups = releaser.current_groups()

    return {
        'name': releaser_or_nick.name,
        'releaser': releaser,
        'groups': groups,
        # use abbreviations for groups if total length of names is 20 or more chars
        'abbreviate_groups': (sum([len(group.name) for group in groups]) >= 20),
    }


@register.inclusion_tag('tags/icon.html')
def icon(icon):
    return {'icon': icon}


@register.inclusion_tag('tags/releaser_flag.html')
def releaser_flag(releaser):
    return {'releaser': releaser}


@register.inclusion_tag('tags/byline.html')
def byline(production):
    return {
        'unparsed_byline': production.unparsed_byline,
        'authors': [(nick, nick.releaser) for nick in production.author_nicks_with_authors()],
        'affiliations': [(nick, nick.releaser) for nick in production.author_affiliation_nicks_with_groups()],
    }


@register.simple_tag
def field_label(field):
    return format_html(u'<label for="{0}" class="field_label">{1}</label>', field.id_for_label, field.label)


@register.simple_tag
def date_range(start_date, end_date):
    if start_date.precision != end_date.precision:
        return "%s - %s" % (start_date.explicit_format(), end_date.explicit_format())
    elif start_date.precision == 'y':
        if start_date.date.year != end_date.date.year:
            return "%s - %s" % (date_format(start_date.date, arg="Y"), date_format(end_date.date, arg="Y"))
        else:
            return date_format(start_date.date, arg="Y")
    elif start_date.precision == 'm':
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


@register.inclusion_tag('tags/last_edited_by.html', takes_context=True)
def last_edited_by(context, item):
    edit = Edit.for_model(item, is_admin=context['request'].user.is_staff).order_by('-timestamp').first()
    return {
        'edit': edit,
        'item': item,
    }


def thumbnail_params_for_size(screenshot, target_width, target_height):
    width, height = screenshot.thumb_dimensions_to_fit(target_width, target_height)

    return {
        'url': screenshot.thumbnail_url,
        'width': width,
        'height': height,
        'natural_width': screenshot.thumbnail_width or 1,
        'natural_height': screenshot.thumbnail_height or 1,
    }


@register.inclusion_tag('tags/thumbnail.html')
def thumbnail(screenshot):
    return thumbnail_params_for_size(screenshot, 133, 100)


@register.inclusion_tag('tags/microthumb.html')
def microthumb(screenshot):
    return thumbnail_params_for_size(screenshot, 48, 36)


@register.inclusion_tag('tags/thumbnail.html')
def megathumb(screenshot):
    width, height = screenshot.thumb_dimensions_to_fit(400, 300)
    return {
        'url': screenshot.standard_url,
        'width': width,
        'height': height,
    }


@register.simple_tag
def site_stats():
    return {
        'production_count': Production.objects.filter(supertype='production').count(),
        'graphics_count': Production.objects.filter(supertype='graphics').count(),
        'music_count': Production.objects.filter(supertype='music').count(),
        'scener_count': Releaser.objects.filter(is_group=False).count(),
        'group_count': Releaser.objects.filter(is_group=True).count(),
        'party_count': Party.objects.count(),
        'bbs_count': BBS.objects.count(),
    }


@register.inclusion_tag('tags/production_listing.html')
def production_listing(productions, show_screenshots=False, show_prod_types=False, mark_excludable=False):
    if show_screenshots:
        screenshots = Screenshot.select_for_production_ids([prod.id for prod in productions])
    else:
        screenshots = {}

    productions_and_screenshots = [
        (production, screenshots.get(production.id))
        for production in productions
    ]
    return {
        'productions_and_screenshots': productions_and_screenshots,
        'show_screenshots': show_screenshots,
        'show_prod_types': show_prod_types,
        'mark_excludable': mark_excludable,
        'site_is_writeable': settings.SITE_IS_WRITEABLE,
    }
