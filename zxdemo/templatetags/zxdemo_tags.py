from django import template

register = template.Library()

@register.inclusion_tag('zxdemo/tags/byline.html')
def byline(production):
	return {
		'unparsed_byline': production.unparsed_byline,
		'authors': [(nick, nick.releaser) for nick in production.author_nicks_with_authors()],
		'affiliations': [(nick, nick.releaser) for nick in production.author_affiliation_nicks_with_groups()],
	}
