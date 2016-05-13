import json
import random

from django.conf import settings
from django.forms import Media
from django.template.loader import render_to_string


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


class Carousel(object):
	def __init__(self, production, user):
		self.production = production
		self.user = user

		self.media = Media()

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

		embeddable_videos = production.links.filter(link_class__in=['YoutubeVideo', 'VimeoVideo']).exclude(thumbnail_url='')
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

		self.items = carousel_data

	def render(self):
		screenshots = [i for i in self.items if i['type'] == 'screenshot']
		if screenshots:
			initial_screenshot = screenshots[0]
		else:
			initial_screenshot = None

		show_all_screenshots_link = len(screenshots) > 1
		if settings.SITE_IS_WRITEABLE:
			show_add_screenshot_link = self.production.can_have_screenshots and self.items
			show_manage_screenshots_link = (self.production.can_have_screenshots or len(screenshots) > 1) and self.user.is_staff
		else:
			show_add_screenshot_link = False
			show_manage_screenshots_link = False

		return render_to_string('productions/_carousel.html', {
			'production': self.production,
			'site_is_writeable': settings.SITE_IS_WRITEABLE,

			'initial_screenshot': initial_screenshot,
			'show_all_screenshots_link': show_all_screenshots_link,
			'show_add_screenshot_link': show_add_screenshot_link,
			'show_manage_screenshots_link': show_manage_screenshots_link,
			'carousel_data': json.dumps(self.items),
		})
