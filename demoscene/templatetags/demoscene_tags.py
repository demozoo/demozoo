from django import template
from django.core.urlresolvers import reverse

from demoscene.models import Releaser, Nick

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

@register.inclusion_tag('shared/byline.html')
def component_byline(authors, affiliations):
	return {
		'unparsed_byline': None,
		'authors': authors,
		'affiliations': affiliations,
	}

@register.simple_tag
def field_label(field):
	return field.label_tag(attrs = {'class': 'field_label'})

@register.inclusion_tag('shared/date_range.html')
def date_range(start_date, end_date):
	return {
		'start_date': start_date,
		'end_date': end_date,
	}


@register.inclusion_tag('shared/thumbnail.html')
def thumbnail(screenshot):
	thumbnail_width = screenshot.thumbnail_width or 1
	thumbnail_height = screenshot.thumbnail_height or 1
	# scale down by whatever factor is required to get both width and height within 133x100
	width_scale = min(133.0 / thumbnail_width, 1)
	height_scale = min(100.0 / thumbnail_height, 1)
	scale = min(width_scale, height_scale)

	width = int(thumbnail_width * scale)
	height = int(thumbnail_height * scale)
	return {
		'url': screenshot.thumbnail_url,
		'width': width,
		'height': height
	}
