from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from freezegun import freeze_time

from homepage.models import Banner, NewsStory
from productions.models import Production


class SimpleTest(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        Banner.objects.create(
            title='Hello anonymous people',
            text='Here is some *markdown*',
            show_for_anonymous_users=True,
            show_for_logged_in_users=False,
        )
        Banner.objects.create(
            title='Hello logged in people',
            text='hello hello hello hello',
            show_for_anonymous_users=False,
            show_for_logged_in_users=True,
        )
        NewsStory.objects.create(
            title='First news item',
            text='''with a <a href="http://example.com/">link</a> in it\nand a <a href="javascript:alert('hacked by limp ninja')">line</a> break ftp://ftp.scene.org/pub/''',
            is_public=True,
        )
        NewsStory.objects.create(
            title='Secret news item',
            text="wooo [fancy link][fancylink]\n\n[fancylink]: http://gasman.zxdemo.org/",
            is_public=False,
        )
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.screenshots.create(
            thumbnail_url='http://example.com/pondlife.thumb.png', thumbnail_width=130, thumbnail_height=100
        )

    def test_fetch_homepage(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Hello anonymous people')
        self.assertContains(response, 'Here is some <em>markdown</em>')

        self.assertNotContains(response, 'Hello logged in people')

        self.assertContains(response, 'First news item')
        self.assertContains(response, 'with a <a href="http://example.com/">link</a> in it<br>\nand a <a>line</a> break <a href="ftp://ftp.scene.org/pub/">ftp://ftp.scene.org/pub/</a>')

        self.assertNotContains(response, 'Secret news item')

    def test_fetch_homepage_as_superuser(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'Hello anonymous people')
        self.assertContains(response, 'Hello logged in people')
        self.assertContains(response, 'First news item')
        self.assertContains(response, 'with a <a href="http://example.com/">link</a> in it')
        self.assertContains(response, 'Secret news item')
        self.assertContains(response, 'wooo <a href="http://gasman.zxdemo.org/">fancy link</a>')

    @freeze_time('2018-12-30')
    def test_date_rollover(self):
        # test separate code path for when 'three months time' rolls over into next year
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
