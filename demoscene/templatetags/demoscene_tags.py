from django import template
from django.utils.html import format_html

from demoscene.models import Releaser, Nick, Edit
from productions.models import Production

register = template.Library()

@register.inclusion_tag('shared/nick_variants.html')
def nick_variants(nick):
	return {'variants': nick.nick_variant_and_abbreviation_list}

@register.inclusion_tag('shared/scener_with_affiliations.html')
def scener_with_affiliations(releaser_or_nick):
	if isinstance(releaser_or_nick, Nick):
		releaser = releaser_or_nick.releaser
	else: # assume a Releaser
		releaser = releaser_or_nick
		name = releaser_or_nick.name
	groups = releaser.current_groups()
	
	return {
		'name': releaser_or_nick.name,
		'releaser': releaser,
		'groups': groups,
		# use abbreviations for groups if total length of names is 20 or more chars
		'abbreviate_groups': (sum([len(group.name) for group in groups]) >= 20),
	}

@register.inclusion_tag('shared/releaser_flag.html')
def releaser_flag(releaser):
	return {'releaser': releaser}

@register.inclusion_tag('shared/byline.html')
def byline(production):
	return {
		'unparsed_byline': production.unparsed_byline,
		'authors': [(nick, nick.releaser) for nick in production.author_nicks_with_authors()],
		'affiliations': [(nick, nick.releaser) for nick in production.author_affiliation_nicks_with_groups()],
	}

@register.simple_tag
def field_label(field):
	return format_html(u'<label for="{0}" class="field_label">{1}</label>', field.id_for_label, field.label)

@register.inclusion_tag('shared/date_range.html')
def date_range(start_date, end_date):
	return {
		'start_date': start_date,
		'end_date': end_date,
	}


@register.inclusion_tag('shared/last_edited_by.html', takes_context=True)
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


@register.inclusion_tag('shared/thumbnail.html')
def thumbnail(screenshot):
	return thumbnail_params_for_size(screenshot, 133, 100)


@register.inclusion_tag('shared/microthumb.html')
def microthumb(screenshot):
	return thumbnail_params_for_size(screenshot, 48, 36)


@register.assignment_tag
def site_stats():
	return {
		'production_count': Production.objects.filter(supertype='production').count(),
		'graphics_count': Production.objects.filter(supertype='graphics').count(),
		'music_count': Production.objects.filter(supertype='music').count(),
		'scener_count': Releaser.objects.filter(is_group=False).count(),
		'group_count': Releaser.objects.filter(is_group=True).count(),
	}
