from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.inclusion_tag('shared/nick_variants.html')
def nick_variants(nick):
	return {'variants': nick.nick_variant_list}
