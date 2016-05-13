import json
import random

from django.conf import settings
from django.forms import Media
from django.template.loader import render_to_string
from django.utils.functional import cached_property


class Carousel(object):
	def __init__(self, production, user):
		self.production = production
		self.user = user

		self.media = Media()

		self.slides = self.get_screenshot_slides()

		if self.videos:
			# prepend a video slide
			self.slides.insert(0, self.get_video_slide())
		elif self.can_make_mosaic():
			# prepend a mosaic slide
			self.slides.insert(0, self.get_mosaic_slide())

	@cached_property
	def screenshots(self):
		"""Return a queryset of this production's screenshots, including not-yet-processed ones"""
		return self.production.screenshots.order_by('id')

	@cached_property
	def processed_screenshots(self):
		"""Return a list of this production's screenshots, excluding not-yet-processed ones"""
		return [s for s in self.screenshots if s.original_url]

	def get_screenshot_slides(self):
		"""Return a list of screenshot slides (including processed ones)"""
		return [
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
			for screenshot in self.screenshots
		]

	@cached_property
	def videos(self):
		"""Return a queryset of external links that are embeddable as videos"""
		return self.production.links.filter(link_class__in=['YoutubeVideo', 'VimeoVideo']).exclude(thumbnail_url='')

	def can_make_mosaic(self):
		"""Do we have enough screenshots to form a mosaic?"""
		return len(self.processed_screenshots) >= 4

	def get_mosaic_data(self):
		"""Return the data dictionary for a mosaic (either as a standalone slide or video background)"""
		return [
			{
				'original_url': screenshot.original_url,
				'standard_url': screenshot.standard_url,
				'standard_width': screenshot.standard_width,
				'standard_height': screenshot.standard_height,
			}
			for screenshot in random.sample(self.processed_screenshots, 4)
		]

	def get_mosaic_slide(self):
		"""Return the data for a standalone mosaic slide"""
		return {
			'type': 'mosaic',
			'id': 'mosaic',
			'is_processing': False,
			'data': self.get_mosaic_data()
		}

	def get_video_slide(self):
		"""Return the data for a video slide"""
		video = self.videos[0]
		video_data = {
			'url': str(video.link),
			'video_width': video.video_width,
			'video_height': video.video_height,
			'embed_code': video.link.get_embed_html(video.video_width, video.video_height),
		}

		if self.can_make_mosaic():
			video_data['mosaic'] = self.get_mosaic_data()
		else:
			# Use a single screenshot as the background - preferably one of ours, if we have one
			if len(self.processed_screenshots) >= 1:
				screenshot = random.choice(self.processed_screenshots)
				thumbnail_url = screenshot.standard_url
				thumbnail_width = screenshot.standard_width
				thumbnail_height = screenshot.standard_height
			else:
				# we don't have any screenshots, so use the probably crappy one extracted from
				# the video provider
				thumbnail_url = video.thumbnail_url
				thumbnail_width = video.thumbnail_width
				thumbnail_height = video.thumbnail_height

			# resize to 400x300 max
			if thumbnail_width > 400 or thumbnail_height > 300:
				scale_factor = min(400.0 / thumbnail_width, 300.0 / thumbnail_height)
				video_data['thumbnail_width'] = round(thumbnail_width * scale_factor)
				video_data['thumbnail_height'] = round(thumbnail_height * scale_factor)
			else:
				video_data['thumbnail_width'] = thumbnail_width
				video_data['thumbnail_height'] = thumbnail_height

			video_data['thumbnail_url'] = thumbnail_url

		return {
			'type': 'video',
			'id': 'video-%d' % video.id,
			'is_processing': False,
			'data': video_data,
		}

	def get_slides_json(self):
		return json.dumps(self.slides)

	def render(self):
		screenshots = [i for i in self.slides if i['type'] == 'screenshot']
		if screenshots:
			initial_screenshot = screenshots[0]
		else:
			initial_screenshot = None

		show_all_screenshots_link = len(screenshots) > 1
		if settings.SITE_IS_WRITEABLE:
			show_add_screenshot_link = self.production.can_have_screenshots and self.slides
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
			'carousel_data': self.get_slides_json(),
		})
