from __future__ import absolute_import, unicode_literals

from comments.models import Comment

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


class TestAddComment(CommentTestCase):
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


class TestEditComment(CommentTestCase):
    def test_cannot_edit_comment_as_anonymous_user(self):
        url = '/productions/%d/comments/%d/edit/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.get(url)
        self.assertRedirects(response, '/account/login/?next=%s' % url)

    def test_cannot_edit_comment_as_non_admin(self):
        self.login()
        url = '/productions/%d/comments/%d/edit/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.get(url)
        self.assertRedirects(response, '/productions/%d/#comment-%d' % (
            self.production.id, self.production_comment.id
        ))

    def test_show_edit_production_comment_form(self):
        self.login_as_admin()
        url = '/productions/%d/comments/%d/edit/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Editing comment for Second Reality</h2>")
        self.assertContains(response, "He is not an atomic playboy.")

    def test_show_edit_party_comment_form(self):
        self.login_as_admin()
        url = '/parties/%d/comments/%d/edit/' % (
            self.party.id, self.party_comment.id
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Editing comment for InerciaDemoparty 2005</h2>")
        self.assertContains(response, "I forgot to come.")

    def test_edit_comment(self):
        self.login_as_admin()
        url = '/productions/%d/comments/%d/edit/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.post(url, {
            'comment-body': "He is still not an atomic playboy."
        })
        self.assertRedirects(response, '/productions/%d/#comment-%d' % (
            self.production.id, self.production_comment.id
        ))
        updated_comment = Comment.objects.get(id=self.production_comment.id)
        self.assertEqual(updated_comment.body, "He is still not an atomic playboy.")

    def test_cannot_edit_empty_comment(self):
        self.login_as_admin()
        url = '/productions/%d/comments/%d/edit/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.post(url, {
            'comment-body': ""
        })
        non_updated_comment = Comment.objects.get(id=self.production_comment.id)
        self.assertEqual(non_updated_comment.body, "He is not an atomic playboy.")
        self.assertEqual(response.status_code, 200)


class TestDeleteComment(CommentTestCase):
    def test_cannot_delete_comment_as_anonymous_user(self):
        url = '/productions/%d/comments/%d/delete/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.get(url)
        self.assertRedirects(response, '/account/login/?next=%s' % url)

    def test_cannot_delete_comment_as_non_admin(self):
        self.login()
        url = '/productions/%d/comments/%d/delete/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.get(url)
        self.assertRedirects(response, '/productions/%d/#comment-%d' % (
            self.production.id, self.production_comment.id
        ))

    def test_show_delete_production_comment_confirmation(self):
        self.login_as_admin()
        url = '/productions/%d/comments/%d/delete/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete this comment?")
        self.assertContains(response, "Deleting comment on Second Reality")

    def test_show_edit_party_comment_form(self):
        self.login_as_admin()
        url = '/parties/%d/comments/%d/delete/' % (
            self.party.id, self.party_comment.id
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete this comment?")
        self.assertContains(response, "Deleting comment on InerciaDemoparty 2005")

    def test_delete_comment(self):
        self.login_as_admin()
        url = '/productions/%d/comments/%d/delete/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.post(url, {
            'yes': 'yes',
        })
        comments = self.production.get_comments()
        self.assertEqual(comments.count(), 1)
        self.assertRedirects(response, '/productions/%d/' % self.production.id)

    def test_decline_delete_comment(self):
        self.login_as_admin()
        url = '/productions/%d/comments/%d/delete/' % (
            self.production.id, self.production_comment.id
        )
        response = self.client.post(url, {
            'no': 'no',
        })
        comments = self.production.get_comments()
        self.assertEqual(comments.count(), 2)
        self.assertRedirects(response, '/productions/%d/#comment-%d' % (
            self.production.id, self.production_comment.id
        ))
