from django import template
from django.core.urlresolvers import reverse

from demoscene.models import Releaser, Nick, Edit

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
		'authors': [(nick, nick.releaser) for nick in production.author_nicks.select_related('releaser')],
		'affiliations': [(nick, nick.releaser) for nick in production.author_affiliation_nicks.select_related('releaser')],
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


@register.inclusion_tag('shared/last_edited_by.html')
def last_edited_by(item):
	try:
		edit = Edit.for_model(item).order_by('-timestamp')[0]
	except IndexError:
		edit = None
	return {
		'edit': edit,
		'item': item,
	}
