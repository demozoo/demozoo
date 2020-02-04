from django import template

from demoscene.templatetags.demoscene_tags import production_listing

register = template.Library()
register.inclusion_tag('awards/_recommended_production_listing.html', name='recommended_production_listing')(production_listing)
