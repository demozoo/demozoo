import json
import random

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.functional import cached_property

from productions.cowbell import get_playable_track_data


class Carousel(object):
    def __init__(self, production, user):
        self.production = production
        self.user = user

        self.media = self.audio_media

        self.slides = self.get_audio_slides() + self.get_screenshot_slides()

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
                'id': 'screenshot-%d' % screenshot.id,
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
            'embed_code': video.link.get_embed_html(video.video_width, video.video_height, autoplay=True),
            'embed_code_without_autoplay': video.link.get_embed_html(video.video_width, video.video_height, autoplay=False),
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

    _audio_tracks = None
    _audio_media = None

    @property
    def audio_tracks(self):
        if self._audio_tracks is None:
            self._audio_tracks, self._audio_media = get_playable_track_data(self.production)
        return self._audio_tracks

    @property
    def audio_media(self):
        if self._audio_media is None:
            self._audio_tracks, self._audio_media = get_playable_track_data(self.production)
        return self._audio_media

    def get_audio_slides(self):
        slides = []
        for track in self.audio_tracks:
            track_data = {
                'url': track['url'],
                'player': track['player'],
                'playerOpts': track['playerOpts'],
            }

            if len(self.processed_screenshots) >= 1:
                artwork = random.choice(self.processed_screenshots)
                track_data['image'] = {
                    'url': artwork.standard_url,
                    'width': artwork.standard_width,
                    'height': artwork.standard_height
                }

            slides.append({
                'type': 'cowbell-audio',
                'id': 'cowbell-%s' % track['id'],
                'is_processing': False,
                'data': track_data
            })

        return slides

    def get_slides_json(self):
        return json.dumps(self.slides)

    def render(self):
        screenshots = [i for i in self.slides if i['type'] == 'screenshot']
        if screenshots:
            initial_screenshot = screenshots[0]
        else:
            initial_screenshot = None

        # for supertype = music, button labels should refer to "artwork" rather than screenshots
        if self.production.supertype == 'music':
            add_screenshot_label = "Add artwork"
            all_screenshots_label = "All artwork"
            manage_screenshots_label = "Manage artwork"
        else:
            add_screenshot_label = "Add screenshot"
            all_screenshots_label = "All screenshots"
            manage_screenshots_label = "Manage screenshots"

        show_all_screenshots_link = len(screenshots) > 1

        prompt_to_edit = settings.SITE_IS_WRITEABLE and (self.user.is_staff or not self.production.locked)
        if prompt_to_edit:
            # always show the 'add screenshot' / 'add artwork' button, except for the special case
            # that supertype is graphics or production and there are no carousel slides -
            # in which case the 'add a screenshot' call-to-action will be in the carousel area instead
            show_add_screenshot_link = self.slides or self.production.supertype == 'music'
            show_manage_screenshots_link = screenshots and self.user.is_staff
        else:
            show_add_screenshot_link = False
            show_manage_screenshots_link = False

        return render_to_string('productions/_carousel.html', {
            'production': self.production,
            'prompt_to_edit': prompt_to_edit,

            'initial_screenshot': initial_screenshot,

            'show_all_screenshots_link': show_all_screenshots_link,
            'all_screenshots_label': all_screenshots_label,

            'show_add_screenshot_link': show_add_screenshot_link,
            'add_screenshot_label': add_screenshot_label,

            'show_manage_screenshots_link': show_manage_screenshots_link,
            'manage_screenshots_label': manage_screenshots_label,

            'carousel_data': self.get_slides_json(),
        })
