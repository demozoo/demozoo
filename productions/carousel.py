def get_carousel_items(production):
	screenshots = production.screenshots.order_by('id')

	carousel_data = [
		{
			'type': 'screenshot',
			'id': 'screenshot-%d' % screenshot.id,
			'is_processing': screenshot.original_url is None,
			'data': {
				'original_url': screenshot.original_url,
				'standard_url': screenshot.standard_url,
				'standard_width': screenshot.standard_width,
				'standard_height': screenshot.standard_height,
			}
		}
		for screenshot in screenshots
	]

	return carousel_data
