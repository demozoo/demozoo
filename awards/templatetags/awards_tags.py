from django import template
from django.conf import settings

from demoscene.templatetags.demoscene_tags import production_listing
from productions.models import Production, Screenshot


register = template.Library()

@register.inclusion_tag('awards/_recommended_production_listing.html')
def recommended_production_listing(recommendations, show_screenshots=False, show_prod_types=False, mark_excludable=False):
    if show_screenshots:
        screenshots = Screenshot.select_for_production_ids([
            recommendation.production.id for recommendation in recommendations
        ])
    else:
        screenshots = {}  # pragma: no cover

    rows = [
        (recommendation, recommendation.production, screenshots.get(recommendation.production.id))
        for recommendation in recommendations
    ]
    return {
        'rows': rows,
        'show_screenshots': show_screenshots,
        'show_prod_types': show_prod_types,
        'mark_excludable': mark_excludable,
        'can_remove_recommendations': settings.SITE_IS_WRITEABLE and rows and rows[0][0].category.event.recommendations_enabled,
    }


register.inclusion_tag('awards/_recommendation_summary_listing.html', name='recommendation_summary_listing')(production_listing)
