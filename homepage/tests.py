from django.core.urlresolvers import reverse
from django.test import TestCase

from homepage.models import Banner, NewsStory


class SimpleTest(TestCase):
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
			text='with a <a href="http://example.com/">link</a> in it',
			is_public=True,
		)
		NewsStory.objects.create(
			title='Secret news item',
			text='wooo',
			is_public=False,
		)

	def test_fetch_homepage(self):
		response = self.client.get(reverse('home'))
		self.assertEqual(response.status_code, 200)

		self.assertContains(response, 'Hello anonymous people')
		self.assertContains(response, 'Here is some <em>markdown</em>')

		self.assertNotContains(response, 'Hello logged in people')

		self.assertContains(response, 'First news item')
		self.assertContains(response, 'with a <a href="http://example.com/" class="external">link</a> in it')

		self.assertNotContains(response, 'Secret news item')
