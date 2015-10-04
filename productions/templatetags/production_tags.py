import json

from django import template

from productions.carousel import get_carousel_items

register = template.Library()


@register.inclusion_tag('productions/_carousel.html', takes_context=True)
def carousel(context, production):
	carousel_items = get_carousel_items(production)
	screenshots = [i for i in carousel_items if i['type'] == 'screenshot']
	if screenshots:
		initial_screenshot = screenshots[0]
	else:
		initial_screenshot = None

	show_all_screenshots_link = len(screenshots) > 1
	if context['site_is_writeable']:
		show_add_screenshot_link = production.can_have_screenshots and carousel_items
		show_manage_screenshots_link = (production.can_have_screenshots or len(screenshots) > 1) and context['user'].is_staff
	else:
		show_add_screenshot_link = False
		show_manage_screenshots_link = False

	return {
		'production': production,
		'site_is_writeable': context['site_is_writeable'],
		'user': context['user'],

		'initial_screenshot': initial_screenshot,
		'show_all_screenshots_link': show_all_screenshots_link,
		'show_add_screenshot_link': show_add_screenshot_link,
		'show_manage_screenshots_link': show_manage_screenshots_link,
		'carousel_data': json.dumps(carousel_items),
	}
