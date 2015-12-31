import random


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
		video_data = {
			'url': str(video.link),
			'video_width': video.video_width,
			'video_height': video.video_height,
			'embed_code': video.link.get_embed_html(video.video_width, video.video_height),
		}

		if len(processed_screenshots) >= 4:
			video_data['mosaic'] = get_mosaic_data(processed_screenshots)
		else:
			if len(processed_screenshots) >= 1:
				screenshot = random.choice(processed_screenshots)
				thumbnail_url = screenshot.standard_url
				thumbnail_width = screenshot.standard_width
				thumbnail_height = screenshot.standard_height
			else:
				thumbnail_url = video.thumbnail_url
				thumbnail_width = video.thumbnail_width
				thumbnail_height = video.thumbnail_height

			if thumbnail_width > 400 or thumbnail_height > 300:
				scale_factor = min(400.0 / thumbnail_width, 300.0 / thumbnail_height)
				video_data['thumbnail_width'] = round(thumbnail_width * scale_factor)
				video_data['thumbnail_height'] = round(thumbnail_height * scale_factor)
			else:
				video_data['thumbnail_width'] = thumbnail_width
				video_data['thumbnail_height'] = thumbnail_height

			video_data['thumbnail_url'] = thumbnail_url

		carousel_data.insert(0, {
			'type': 'video',
			'id': 'video-%d' % video.id,
			'is_processing': False,
			'data': video_data,
		})
	elif len(processed_screenshots) >= 4:
		carousel_data.insert(0, {
			'type': 'mosaic',
			'id': 'mosaic',
			'is_processing': False,
			'data': get_mosaic_data(processed_screenshots)
		})

	return carousel_data
