import random
import json


def get_mosaic_data(processed_screenshots):
	return [
		{
			'original_url': screenshot.original_url,
			'standard_url': screenshot.standard_url,
			'standard_width': screenshot.standard_width,
			'standard_height': screenshot.standard_height,
		}
		for screenshot in random.sample(processed_screenshots, 4)
	]


def get_video_data(video):
	if video.thumbnail_width > 400 or video.thumbnail_height > 300:
		scale_factor = min(400.0 / video.thumbnail_width, 300.0 / video.thumbnail_height)
		width = round(video.thumbnail_width * scale_factor)
		height = round(video.thumbnail_height * scale_factor)
	else:
		width = video.thumbnail_width
		height = video.thumbnail_height

	return {
		'url': str(video.link),
		'oembed_data': json.loads(video.oembed_data),
		'thumbnail_url': video.thumbnail_url,
		'thumbnail_width': width,
		'thumbnail_height': height
	}


def get_carousel_items(production):
	screenshots = production.screenshots.order_by('id')
	processed_screenshots = [s for s in screenshots if s.original_url]

	embeddable_videos = production.links.filter(link_class__in=['YoutubeVideo', 'VimeoVideo']).exclude(thumbnail_url='')

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

	if embeddable_videos:
		video = embeddable_videos[0]
		carousel_data.insert(0, {
			'type': 'video',
			'id': 'video-%d' % video.id,
			'is_processing': False,
			'data': get_video_data(video)
		})
	elif len(processed_screenshots) >= 4:
		carousel_data.insert(0, {
			'type': 'mosaic',
			'id': 'mosaic',
			'is_processing': False,
			'data': get_mosaic_data(processed_screenshots)
		})

	return carousel_data
