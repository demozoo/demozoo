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
		gasman_productions = sorted([prod.title for prod in gasman.productions()])
		self.assertEqual(gasman_productions, ["Madrielle", "Mooncheese"])

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

		raww_arse_member_prods = sorted(
			[prod.title for prod in raww_arse.member_productions()]
		)

		# "Fakeprod" should be returned because it is authored by "Fakescener / Raww Arse",
		#     even though Fakescener is not actually a member of Raww Arse
		# "Madrielle" should be returned because it is authored by "Gasman / Raww Arse"
		# "Laesq24 Giftro" should be returned because it is by Papaya Dezign,
		#     a subgroup of Raww Arse, even though the byline doesn't mention Raww Arse
		self.assertEqual(
			raww_arse_member_prods,
			["Fakeprod", "Laesq24 Giftro", "Madrielle"]
		)


class TestReleaserCredits(TestCase):
	fixtures = ['tests/gasman.json']

	def test_get_credits(self):
		gasman = Releaser.objects.get(name="Gasman")
		gasman_credits = sorted([
			(credit.production.title, credit.category)
			for credit in gasman.credits()
		])
		self.assertEqual(
			gasman_credits,
			[("Pondlife", "Code")]
		)


class TestReleaserGroups(TestCase):
	fixtures = ['tests/gasman.json']

	def test_get_groups(self):
		yerzmyey = Releaser.objects.get(name="Yerzmyey")
		yerzmyey_groups = sorted([group.name for group in yerzmyey.groups()])
		self.assertEqual(yerzmyey_groups, ["Hooy-Program", "Raww Arse"])

	def test_get_current_groups(self):
		yerzmyey = Releaser.objects.get(name="Yerzmyey")
		yerzmyey_groups = sorted([group.name for group in yerzmyey.current_groups()])
		self.assertEqual(yerzmyey_groups, ["Hooy-Program"])
