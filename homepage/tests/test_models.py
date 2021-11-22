import re
from io import BytesIO

import PIL.Image
from django.core.files.images import ImageFile
from django.test import TestCase

from homepage.models import Banner, BannerImage, NewsImage, NewsStory


def get_test_image():
    f = BytesIO()
    image = PIL.Image.new('RGBA', (200, 200), 'white')
    image.save(f, 'PNG')
    return ImageFile(f, name='test.png')


class TestBannerModel(TestCase):
    def test_str(self):
        banner = Banner.objects.create(
            title='Revision 2020',
            text='welcome home',
            show_for_anonymous_users=True,
            show_for_logged_in_users=True,
        )
        self.assertEqual(str(banner), "Revision 2020")


class TestBannerImageModel(TestCase):
    def setUp(self):
        self.banner_image = BannerImage.objects.create(
            image=get_test_image(), image_url='http://example.com/test.png'
        )

    def test_str(self):
        self.assertTrue(re.match(r'homepage_banners/\w/\w/\w+.png', str(self.banner_image)))

    def test_image_tag(self):
        self.assertEqual(self.banner_image.image_tag(), '<img src="http://example.com/test.png" width="400" alt="" />')


class TestNewsStoryModel(TestCase):
    def test_str(self):
        news = NewsStory.objects.create(
            title='Norway goat cheese fire closes tunnel',
            text='A road tunnel in Norway has been closed - by a lorry-load of burning cheese.',
            is_public=True,
        )
        self.assertEqual(str(news), "Norway goat cheese fire closes tunnel")


class TestNewsImageModel(TestCase):
    def setUp(self):
        self.news_image = NewsImage.objects.create(
            image=get_test_image(), image_url='http://example.com/test.png'
        )

    def test_str(self):
        self.assertTrue(re.match(r'news_images/\w/\w/\w+.png', str(self.news_image)))

    def test_image_tag(self):
        self.assertEqual(self.news_image.image_tag(), '<img src="http://example.com/test.png" width="100" alt="" />')
