from django import template


register = template.Library()


@register.inclusion_tag('productions/_core_details.html', takes_context=True)
def production_core_details(context, production, subpage=False):
	ctx = {
		'production': production,
		'invitation_parties': production.invitation_parties.order_by('start_date_date'),
		'release_parties': production.release_parties.order_by('start_date_date'),
		'competition_placings': production.competition_placings.select_related('competition__party').order_by('competition__party__start_date_date'),
	}
	if subpage:
		ctx.update({
			'show_back_button': True,
		})
	else:
		ctx.update({
			'show_edit_button': context['site_is_writeable'],
			'show_back_button': False,
		})

	return ctx
