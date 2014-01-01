from django import template
from django.db.models import Q

from parties.models import Party
import datetime

register = template.Library()

@register.inclusion_tag('zxdemo/tags/byline.html')
def byline(production):
	return {
		'unparsed_byline': production.unparsed_byline,
		'authors': [(nick, nick.releaser) for nick in production.author_nicks_with_authors()],
		'affiliations': [(nick, nick.releaser) for nick in production.author_affiliation_nicks_with_groups()],
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
