import random


def get_carousel_items(production):
	screenshots = production.screenshots.order_by('id')

	processed_screenshots = [s for s in screenshots if s.original_url]

	carousel_data = [
		{
			'type': 'screenshot',
			'id': 'screenshot-%d' % screenshot.id,
			'is_processing': not screenshot.original_url,
			'data': {
				'original_url': screenshot.original_url,
				'standard_url': screenshot.standard_url,
				'standard_width': screenshot.standard_width,
				'standard_height': screenshot.standard_height,
			}
		}
		for screenshot in screenshots
	]

	if len(processed_screenshots) >= 4:
		carousel_data.insert(0, {
			'type': 'mosaic',
			'id': 'mosaic',
			'is_processing': False,
			'data': [
				{
					'original_url': screenshot.original_url,
					'standard_url': screenshot.standard_url,
					'standard_width': screenshot.standard_width,
					'standard_height': screenshot.standard_height,
				}
				for screenshot in random.sample(processed_screenshots, 4)
			]
		})

	return carousel_data
