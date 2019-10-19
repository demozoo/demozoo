# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from demoscene.models import Releaser, Nick
from productions.models import Production


class TestReleaser(TestCase):
    def setUp(self):
        self.gasman = Releaser.objects.create(
            name="Gasman",
            is_group=False,
            location="Århus, Denmark",
            notes="arrest this man, he talks in <i>maths</i>",
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

    def test_asciified_location(self):
        self.assertEqual(self.gasman.asciified_location, "Arhus, Denmark")

    def test_plaintext_notes(self):
        self.assertEqual(self.gasman.plaintext_notes, "arrest this man, he talks in maths")


class TestRealName(TestCase):
    fixtures = ['tests/gasman.json']

    def test_full_name(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman.show_surname = True
        self.assertEqual(gasman.public_real_name, "Matt Westcott")

    def test_surname_only(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman.show_surname = True
        gasman.show_first_name = False
        self.assertEqual(gasman.public_real_name, "Westcott")

    def test_no_name(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman.show_surname = False
        gasman.show_first_name = False
        self.assertEqual(gasman.public_real_name, None)

    def test_asciified_real_name(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman.first_name = "Bjørn"
        self.assertEqual(gasman.asciified_real_name, "Bjorn Westcott")

    def test_asciified_public_real_name(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman.first_name = "Bjørn"
        self.assertEqual(gasman.asciified_public_real_name, "Bjorn")


class TestReleaserProductions(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get_productions(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman_productions = sorted([prod.title for prod in gasman.productions()])
        self.assertIn("Madrielle", gasman_productions)
        self.assertIn("Mooncheese", gasman_productions)

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

    def test_bad_primary_nick(self):
        gasman = Releaser.objects.filter(name="Gasman").prefetch_related('nicks').first()
        gasman.name = 'not gasman'
        with self.assertRaises(Nick.DoesNotExist):
            gasman.primary_nick

    def test_multiple_primary_nicks(self):
        Nick.objects.create(releaser=Releaser.objects.get(name="Gasman"), name="not gasman")
        gasman = Releaser.objects.filter(name="Gasman").prefetch_related('nicks').first()
        for nick in gasman.nicks.all():
            if nick.name == 'not gasman':
                nick.name = 'Gasman'

        with self.assertRaises(Nick.MultipleObjectsReturned):
            gasman.primary_nick

    def test_abbreviation(self):
        raww_arse = Releaser.objects.get(name="Raww Arse")
        self.assertEqual(raww_arse.abbreviation, "RA")

        papaya_dezign = Releaser.objects.get(name="Papaya Dezign")
        self.assertFalse(papaya_dezign.abbreviation)

    def test_alternative_nicks(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman_nicks = sorted([nick.name for nick in gasman.alternative_nicks])
        self.assertEqual(gasman_nicks, ["Shingebis"])

    def test_all_names_string(self):
        gasman = Releaser.objects.get(name="Gasman")
        self.assertEqual(gasman.all_names_string, "Gasman, Shingebis")

    def test_all_names_string_prefetched(self):
        gasman = Releaser.objects.filter(name="Gasman").prefetch_related('nicks__variants').first()
        with self.assertNumQueries(0):
            self.assertEqual(gasman.all_names_string, "Gasman, Shingebis")

    def test_asciified_all_names_string(self):
        gasman = Releaser.objects.get(name="Gasman")
        gasman.primary_nick.name = "Gåsman"
        self.assertEqual(gasman.asciified_all_names_string, "Gasman, Shingebis")

    def test_all_affiliation_names_string(self):
        gasman = Releaser.objects.get(name="Gasman")
        self.assertEqual(gasman.all_affiliation_names_string, "Hooy-Program, Raww Arse")

    def test_nick_from_id_and_name(self):
        okkie = Nick.from_id_and_name("newscener", "Okkie")
        self.assertEqual(okkie.name, "Okkie")
        self.assertFalse(okkie.releaser.is_group)

        poobrain = Nick.from_id_and_name("newgroup", "Poo-Brain")
        self.assertEqual(poobrain.name, "Poo-Brain")
        self.assertTrue(poobrain.releaser.is_group)

        gasman = Nick.from_id_and_name(Nick.objects.get(name="Gasman").id, "Gasman")
        self.assertEqual(gasman.name, "Gasman")
        self.assertFalse(gasman.releaser.is_group)

    def test_rewrite_nick_variant_list(self):
        gasman = Releaser.objects.get(name="Gasman").primary_nick
        gasman.nick_variant_list = "Gasman, GasBloke"
        self.assertEqual(gasman.nick_variant_list, "Gasman, GasBloke")

    def test_changing_primary_nick_changes_releaser_name(self):
        gasman_nick = Releaser.objects.get(name="Gasman").primary_nick
        gasman_nick.name = "GasBloke"
        gasman_nick.save()
        self.assertTrue(Releaser.objects.filter(name="GasBloke").exists())

    def test_cannot_delete_primary_nick_by_reassignment(self):
        gasman_nick = Releaser.objects.get(name="Gasman").primary_nick
        with self.assertRaises(Exception):
            gasman_nick.reassign_references_and_delete()
        self.assertTrue(Nick.objects.filter(name="Gasman").exists())
