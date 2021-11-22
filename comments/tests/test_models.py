from comments.models import Comment

from .utils import CommentTestCase


class TestCommentModel(CommentTestCase):
    def test_production_comment_url(self):
        expected_url = '/productions/%d/#comment-%d' % (
            self.production.id, self.production_comment.id
        )

        self.assertEqual(self.production_comment.get_absolute_url(), expected_url)

    def test_party_comment_url(self):
        expected_url = '/parties/%d/#comment-%d' % (
            self.party.id, self.party_comment.id
        )

        self.assertEqual(self.party_comment.get_absolute_url(), expected_url)

    def test_get_comments(self):
        comments = list(self.production.get_comments())
        self.assertEqual(comments, [self.production_comment, self.second_production_comment])

    def test_comment_timestamps_are_auto_populated(self):
        comment = Comment.objects.create(
            user=self.user,
            commentable=self.production,
            body="ten seconds to transmission",
        )

        self.assertNotEqual(comment.created_at, None)
        self.assertNotEqual(comment.updated_at, None)

        original_created_at = comment.created_at
        original_updated_at = comment.updated_at

        comment.body = "nine seconds to transmission"
        comment.save()
        self.assertEqual(comment.created_at, original_created_at)
        self.assertNotEqual(comment.updated_at, original_updated_at)
