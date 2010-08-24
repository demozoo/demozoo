from django import template
from django.core.urlresolvers import reverse

from demoscene.models import Releaser, Nick

register = template.Library()

@register.inclusion_tag('shared/nick_variants.html')
def nick_variants(nick):
	return {'variants': nick.nick_variant_and_abbreviation_list}

@register.inclusion_tag('shared/scener_with_affiliations.html')
def scener_with_affiliations(scener):
	if isinstance(scener, Nick):
		return {
			'name': scener.name,
			'releaser': scener.releaser,
			'groups': scener.releaser.groups.all()
		}
	else: # assume a Releaser
		return {
			'name': scener.name,
			'releaser': scener,
			'groups': scener.groups.all()
		}

@register.inclusion_tag('shared/releaser_flag.html')
def releaser_flag(releaser):
	return {'releaser': releaser}
