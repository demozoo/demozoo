from __future__ import unicode_literals

import datetime

from django.test import TestCase

from demoscene.models import Releaser, Nick
from productions.models import Production


class TestReleaser(TestCase):
	def setUp(self):
		self.gasman = Releaser.objects.create(
			name="Gasman",
			is_group=False,
			updated_at=datetime.datetime.now()  # FIXME: having to pass updated_at is silly
		)
		self.hooy_program = Releaser.objects.create(
			name="Hooy-Program",
			is_group=True,
			updated_at=datetime.datetime.now()
		)

	def test_releaser_nick_creation(self):
		# creating a releaser should create a corresponding Nick object
		self.assertEqual(Nick.objects.filter(name="Gasman").count(), 1)

	def test_string_repr(self):
		self.assertEqual(str(self.gasman), "Gasman")

	def test_search_template(self):
		self.assertEqual(
			self.gasman.search_result_template(),
			'search/results/scener.html'
		)

		self.assertEqual(
			self.hooy_program.search_result_template(),
			'search/results/group.html'
		)

	def test_url(self):
		self.assertEqual(
			self.gasman.get_absolute_url(),
			'/sceners/%d/' % self.gasman.id
		)

		self.assertEqual(
			self.hooy_program.get_absolute_url(),
			'/groups/%d/' % self.hooy_program.id
		)

	def test_history_url(self):
		self.assertEqual(
			self.gasman.get_history_url(),
			'/sceners/%d/history/' % self.gasman.id
		)

		self.assertEqual(
			self.hooy_program.get_history_url(),
			'/groups/%d/history/' % self.hooy_program.id
		)


class TestReleaserProductions(TestCase):
	fixtures = ['tests/gasman.json']

	def test_get_productions(self):
		gasman = Releaser.objects.get(name="Gasman")
		gasman_productions = gasman.productions().order_by('title')
		self.assertEqual(
			list(gasman_productions.values_list('title', flat=True)),
			["Madrielle", "Mooncheese"]
		)

	def test_get_member_productions(self):
		raww_arse = Releaser.objects.get(name="Raww Arse")

		# Create a fake prod credited to Fakescener / Raww Arse,
		# to check that prods can still be returned as member prods
		# even if the author is not actually a member of the group
		fakescener = Releaser.objects.create(
			name="Fakescener",
			is_group=False,
			updated_at=datetime.datetime.now()  # FIXME: having to pass updated_at is silly
		)
		fakeprod = Production.objects.create(
			title="Fakeprod",
			updated_at=datetime.datetime.now()
		)
		fakeprod.author_nicks.add(fakescener.nicks.first())
		fakeprod.author_affiliation_nicks.add(raww_arse.nicks.first())

		raww_arse_member_prods = raww_arse.member_productions().order_by('title')

		# "Fakeprod" should be returned because it is authored by "Fakescener / Raww Arse",
		#     even though Fakescener is not actually a member of Raww Arse
		# "Madrielle" should be returned because it is authored by "Gasman / Raww Arse"
		# "Laesq24 Giftro" should be returned because it is by Papaya Dezign,
		#     a subgroup of Raww Arse, even though the byline doesn't mention Raww Arse
		self.assertEqual(
			list(raww_arse_member_prods.values_list('title', flat=True)),
			["Fakeprod", "Laesq24 Giftro", "Madrielle"]
		)


class TestReleaserCredits(TestCase):
	fixtures = ['tests/gasman.json']

	def test_get_credits(self):
		gasman = Releaser.objects.get(name="Gasman")
		gasman_credits = gasman.credits().order_by('production__title')
		self.assertEqual(
			list(gasman_credits.values_list('production__title', 'category')),
			[("Pondlife", "Code")]
		)
