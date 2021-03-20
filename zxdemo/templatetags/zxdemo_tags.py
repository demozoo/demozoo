from __future__ import absolute_import, unicode_literals

import datetime

from django import template
from django.conf import settings
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from parties.models import Party
from zxdemo.models import spectrum_releasers


register = template.Library()

@register.inclusion_tag('zxdemo/tags/byline.html', takes_context=True)
def byline(context, production, check_spectrum=False):
    if check_spectrum:
        try:
            spectrum_releaser_ids = context['spectrum_releaser_ids']
        except KeyError:
            spectrum_releaser_ids = set(spectrum_releasers().values_list('id', flat=True))
            context['spectrum_releaser_ids'] = spectrum_releaser_ids

        authors = [(nick, nick.releaser_id in spectrum_releaser_ids) for nick in production.author_nicks.all()]
        affiliations = [(nick, nick.releaser_id in spectrum_releaser_ids) for nick in production.author_affiliation_nicks.all()]
    else:
        authors = [(author, True) for author in production.author_nicks.all()]
        affiliations = [(affiliation, True) for affiliation in production.author_affiliation_nicks.all()]

    return {
        'unparsed_byline': production.unparsed_byline,
        'authors': authors,
        'affiliations': affiliations,
    }

@register.inclusion_tag('zxdemo/tags/forthcoming_parties.html')
def forthcoming_parties():
    # TODO: only show ones that have been marked as having Spectrum relevance?
    date_filter = Q(start_date_date__gte=datetime.date.today()) | Q(end_date_date__gte=datetime.date.today())
    return {
        'parties': Party.objects.filter(date_filter).order_by('start_date_date', 'end_date_date')
    }

@register.inclusion_tag('zxdemo/tags/date_range.html')
def date_range(start_date, end_date):
    return {
        'start_date': start_date,
        'end_date': end_date,
    }


DOWNLOAD_TYPE_ICONS = [
    ('soundtrack', 'track_new.gif'),
    ('VTX', 'chipmusic_new.gif'),
    ('TAP', 'tape_new.gif'),
    ('SCL', 'disc_new.gif'),
    ('custom TAP', 'specialtape_new.gif'),
    ('TZX', 'specialtape_new.gif'),
    ('DivX', 'video_new.gif'),
    ('Z80', 'z80.gif'),
    ('AY', 'ay.gif'),
]
@register.simple_tag
def download_icon(download):
    icon_filename = 'disc_new.gif'
    if download.description:
        for prefix, filename in DOWNLOAD_TYPE_ICONS:
            if download.description.startswith(prefix):
                icon_filename = filename
                break

    return format_html(
        '<img src="/static/zxdemo/images/icon/{}" alt="" width="24" height="24" border="0" />',
        icon_filename
    )


@register.simple_tag
def production_type_icon(production):
    if production.supertype == 'graphics':
        return mark_safe('<img src="/static/zxdemo/images/icon/gfx_new.gif" align="absmiddle" alt="[Graphics]" width="24" height="24" border="0" />')
    elif production.supertype == 'music':
        return mark_safe('<img src="/static/zxdemo/images/icon/music_new.gif" align="absmiddle" alt="[Music]" width="24" height="24" border="0" />')
    else:
        return mark_safe('<img src="/static/zxdemo/images/icon/demo_new.gif" align="absmiddle" alt="[Demo]" width="24" height="24" border="0" />')


@register.filter
def is_spectrum_production(production):
    return any([(platform.id in settings.ZXDEMO_PLATFORM_IDS) for platform in production.platforms.all()])


@register.filter
def in_groups_of(items, count):
    return [items[i:i+count] for i in range(0, len(items), count)]
