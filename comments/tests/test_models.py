from __future__ import unicode_literals

import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from fuzzy_date import FuzzyDate

from productions.models import Production
from parties.models import PartySeries, Party
from comments.models import Comment


class TestCommentModel(TestCase):
	def setUp(self):
		self.user = User.objects.create(username='bob')
		self.production = Production.objects.create(
			title="Second Reality",
		)
		self.production_comment = Comment.objects.create(
			user=self.user,
			commentable=self.production,
			body="He is not an atomic playboy.",
			created_at=datetime.datetime(2014, 1, 1)
		)
		self.second_production_comment = Comment.objects.create(
			user=self.user,
			commentable=self.production,
			body="On second thoughts, maybe he is.",
			created_at=datetime.datetime(2014, 1, 2)
		)
		self.party_series = PartySeries.objects.create(name="InerciaDemoparty")
		self.party = Party.objects.create(
			party_series=self.party_series,
			start_date=FuzzyDate.parse('2005'),
			end_date=FuzzyDate.parse('2005'),
			name="InerciaDemoparty 2005"
		)
		self.party_comment = Comment.objects.create(
			user=self.user,
			commentable=self.party,
			body="I forgot to come."
		)

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
