from django import template
from django.conf import settings

from productions.models import Production, Screenshot


register = template.Library()

@register.inclusion_tag('awards/_recommended_production_listing.html')
def recommended_production_listing(recommendations, show_screenshots=False, show_prod_types=False, mark_excludable=False):
    if show_screenshots:
        screenshots = Screenshot.select_for_production_ids([
            recommendation.production.id for recommendation in recommendations
        ])
    else:
        screenshots = {}

    rows = [
        (recommendation, recommendation.production, screenshots.get(recommendation.production.id))
        for recommendation in recommendations
    ]
    return {
        'rows': rows,
        'show_screenshots': show_screenshots,
        'show_prod_types': show_prod_types,
        'mark_excludable': mark_excludable,
        'site_is_writeable': settings.SITE_IS_WRITEABLE,
    }
