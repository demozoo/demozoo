from __future__ import absolute_import, unicode_literals

from .utils import CommentTestCase


class TestShowComments(CommentTestCase):
	def test_show_comments(self):
		response = self.client.get('/productions/%d/' % self.production.id)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "2 comments")
		self.assertContains(response, "bob the commenter")
		self.assertContains(response, "He is not an atomic playboy.")
		self.assertNotContains(response, "Be the first to comment on this production...")

	def test_show_uncommented_production(self):
		response = self.client.get('/productions/%d/' % self.uncommented_production.id)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Be the first to comment on this production...")

	def test_add_comment_requires_login(self):
		url = '/productions/%d/comments/new/' % self.uncommented_production.id
		response = self.client.get(url)
		self.assertRedirects(response, '/account/login/?next=%s' % url)

	def test_show_add_production_comment_form(self):
		self.login()
		url = '/productions/%d/comments/new/' % self.uncommented_production.id
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "<h2>Adding a comment for BITS 99</h2>")

	def test_show_add_party_comment_form(self):
		self.login()
		url = '/parties/%d/comments/new/' % self.party.id
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "<h2>Adding a comment for InerciaDemoparty 2005</h2>")

	def test_add_comment(self):
		self.login()
		url = '/productions/%d/comments/new/' % self.uncommented_production.id
		response = self.client.post(url, {
			'comment-body': "wow such colourful"
		})

		comments = self.uncommented_production.get_comments()
		self.assertEqual(comments.count(), 1)
		self.assertRedirects(response, '/productions/%d/#comment-%d' % (
			self.uncommented_production.id, comments.get().id
		))

	def test_cannot_add_empty_comment(self):
		self.login()
		url = '/productions/%d/comments/new/' % self.uncommented_production.id
		response = self.client.post(url, {
			'comment-body': ""
		})

		comments = self.uncommented_production.get_comments()
		self.assertEqual(comments.count(), 0)
		self.assertEqual(response.status_code, 200)
