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
        )
        self.hooy_program = Releaser.objects.create(
            name="Hooy-Program",
            is_group=True,
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
        )
        fakeprod = Production.objects.create(
            title="Fakeprod",
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
        with self.assertNumQueries(1):
            yerzmyey_groups = sorted([group.name for group in yerzmyey.groups()])
            self.assertEqual(yerzmyey_groups, ["Hooy-Program", "Raww Arse"])

    def test_get_current_groups(self):
        yerzmyey = Releaser.objects.get(name="Yerzmyey")
        with self.assertNumQueries(1):
            yerzmyey_groups = sorted([group.name for group in yerzmyey.current_groups()])
            self.assertEqual(yerzmyey_groups, ["Hooy-Program"])

    def test_current_groups_should_use_prefetch_cache(self):
        yerzmyey = Releaser.objects.filter(name="Yerzmyey").prefetch_related('group_memberships__group').first()
        with self.assertNumQueries(0):
            yerzmyey_groups = sorted([group.name for group in yerzmyey.current_groups()])
            self.assertEqual(yerzmyey_groups, ["Hooy-Program"])

    def test_members(self):
        # should include subgroups and ex-members
        raww_arse = Releaser.objects.get(name="Raww Arse")
        with self.assertNumQueries(1):
            raww_arse_members = sorted([member.name for member in raww_arse.members()])
            self.assertEqual(
                raww_arse_members,
                ["Gasman", "LaesQ", "Papaya Dezign", "Yerzmyey"]
            )


class TestReleaserString(TestCase):
    fixtures = ['tests/gasman.json']

    def test_name_with_affiliations(self):
        yerzmyey = Releaser.objects.get(name="Yerzmyey")
        # groups list should not contain ex-groups;
        # this one is short enough to not need abbreviation
        self.assertEqual(yerzmyey.name_with_affiliations(), "Yerzmyey / Hooy-Program")

        gasman = Releaser.objects.get(name="Gasman")
        # groups list in full is >=20 chars, so abbreviate
        self.assertEqual(gasman.name_with_affiliations(), "Gasman / H-Prg ^ RA")

        laesq = Releaser.objects.get(name="LaesQ")
        # do not abbreviate groups that don't have abbreviations (duh)
        self.assertEqual(laesq.name_with_affiliations(), "LaesQ / Papaya Dezign ^ RA")


class TestReleaserNicks(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get_primary_nick(self):
        gasman = Releaser.objects.get(name="Gasman")
        self.assertEqual(gasman.primary_nick, Nick.objects.get(name="Gasman"))

    def test_primary_nick_should_use_prefetch_cache(self):
        gasman = Releaser.objects.filter(name="Gasman").prefetch_related('nicks').first()
        with self.assertNumQueries(0):
            self.assertEqual(gasman.primary_nick.name, "Gasman")

    def test_abbreviation(self):
        raww_arse = Releaser.objects.get(name="Raww Arse")
        self.assertEqual(raww_arse.abbreviation, "RA")

        papaya_dezign = Releaser.objects.get(name="Papaya Dezign")
        self.assertFalse(papaya_dezign.abbreviation)

    def test_alternative_nicks(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman_nicks = sorted([nick.name for nick in gasman.alternative_nicks])
        self.assertEqual(gasman_nicks, ["Shingebis"])
