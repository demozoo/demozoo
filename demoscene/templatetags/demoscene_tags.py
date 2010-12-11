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
		'production': production,
		'author_nicks': production.author_nicks.all(),
		'author_affiliation_nicks': production.author_affiliation_nicks.all(),
	}
