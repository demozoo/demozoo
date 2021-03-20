from __future__ import absolute_import, unicode_literals

import datetime

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from mock import patch

from demoscene.models import Edit, Releaser
from platforms.models import Platform
from productions.models import Production


class TestFillJanewayReleaseDates(TestCase):
    fixtures = ['tests/janeway.json']

    def test_run(self):
        sota = Production.objects.create(
            title="State Of The Art", supertype="production"
        )
        sota.links.create(link_class='KestraBitworldRelease', parameter=345)
        with captured_stdout():
            call_command('fill_janeway_release_dates')

        self.assertEqual(
            Production.objects.get(pk=sota.pk).release_date_date,
            datetime.date(1992, 12, 29)
        )


class TestImportJanewayScreenshots(TestCase):
    fixtures = ['tests/janeway.json']

    @patch('janeway.tasks.import_screenshot')
    def test_run(self, import_screenshot):
        sota = Production.objects.create(
            title="State Of The Art", supertype="production"
        )
        sota.links.create(link_class='KestraBitworldRelease', parameter=345)
        with captured_stdout():
            call_command('import_janeway_screenshots')

        self.assertEqual(import_screenshot.delay.call_count, 1)
        production_id, screenshot_janeway_id, screenshot_url, screenshot_suffix = import_screenshot.delay.call_args.args
        self.assertEqual(production_id, sota.id)
        self.assertEqual(screenshot_janeway_id, 111)
        self.assertEqual(screenshot_url, "http://kestra.exotica.org.uk/files/screenies/28000/154a.png")
        self.assertEqual(screenshot_suffix, "a")


class TestImportJanewayUnknownAuthors(TestCase):
    fixtures = ['tests/janeway.json']

    def test_run(self):
        with captured_stdout():
            call_command('import_janeway_unknown_authors')

        self.assertTrue(Releaser.objects.filter(name="Spaceballs").exists())


class TestMatchJanewayGroups(TestCase):
    fixtures = ['tests/janeway.json']

    def test_match_by_member_name(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        tmb = Releaser.objects.create(name="TMB Designs", is_group=False)
        spb.member_memberships.create(member=tmb)
        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        spb.member_memberships.create(member=slummy)

        with captured_stdout():
            call_command('match_janeway_groups')

        self.assertTrue(
            spb.external_links.filter(link_class='KestraBitworldAuthor', parameter='123').exists()
        )

    def test_match_by_member_id(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        spb.member_memberships.create(member=slummy)
        slummy.external_links.create(link_class='KestraBitworldAuthor', parameter='126')

        with captured_stdout():
            call_command('match_janeway_groups')

        self.assertTrue(
            spb.external_links.filter(link_class='KestraBitworldAuthor', parameter='123').exists()
        )


class TestMatchJanewayMemberships(TestCase):
    fixtures = ['tests/janeway.json']

    def test_run(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class='KestraBitworldAuthor', parameter='123')

        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        slummy.external_links.create(link_class='KestraBitworldAuthor', parameter='126')

        with captured_stdout():
            call_command('match_janeway_memberships')

        self.assertTrue(
            spb.member_memberships.filter(member=slummy, data_source='janeway').exists()
        )

    def test_group_not_found(self):
        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        slummy.external_links.create(link_class='KestraBitworldAuthor', parameter='126')

        with captured_stdout():
            call_command('match_janeway_memberships')

        self.assertEqual(
            slummy.group_memberships.count(), 0
        )

    def test_existing_membership(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class='KestraBitworldAuthor', parameter='123')

        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        slummy.external_links.create(link_class='KestraBitworldAuthor', parameter='126')
        spb.member_memberships.create(member=slummy, is_current=True)

        with captured_stdout():
            call_command('match_janeway_memberships')

        self.assertFalse(
            spb.member_memberships.filter(member=slummy, data_source='janeway').exists()
        )

    def test_deleted_membership(self):
        """
        don't create a membership entry from Janeway data if a membership for that
        member and group was previously deleted
        """
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class='KestraBitworldAuthor', parameter='123')

        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        slummy.external_links.create(link_class='KestraBitworldAuthor', parameter='126')

        user = User.objects.create_user(username='testuser', password='12345')
        Edit.objects.create(
            action_type='remove_membership', focus=slummy, focus2=spb,
            user=user,
            description="Removed Slummy's membership of Spaceballs"
        )

        with captured_stdout():
            call_command('match_janeway_memberships')

        self.assertFalse(
            spb.member_memberships.filter(member=slummy).exists()
        )


class TestMatchJanewayProductions(TestCase):
    fixtures = ['tests/janeway.json']

    def test_run(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class='KestraBitworldAuthor', parameter='123')

        sota = Production.objects.create(
            title="State Of The Art", supertype="production"
        )
        sota.platforms.add(Platform.objects.get(name="Amiga OCS/ECS"))
        sota.author_nicks.add(spb.primary_nick)

        with captured_stdout():
            call_command('match_janeway_productions')

        self.assertTrue(
            sota.links.filter(link_class='KestraBitworldRelease', parameter='345', source='janeway-automatch').exists()
        )

        nkotbb = Production.objects.get(title="New kids on the boot block")
        self.assertEqual(nkotbb.data_source, "janeway")
        self.assertTrue(
            nkotbb.links.filter(link_class='KestraBitworldRelease', parameter='351').exists()
        )


class TestMatchJanewaySceners(TestCase):
    fixtures = ['tests/janeway.json']

    def test_match_by_group_id(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class='KestraBitworldAuthor', parameter='123')

        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        spb.member_memberships.create(member=slummy)

        with captured_stdout():
            call_command('match_janeway_sceners')

        self.assertTrue(
            slummy.external_links.filter(link_class='KestraBitworldAuthor', parameter='126').exists()
        )

    def test_match_by_group_name(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        bzh = Releaser.objects.create(name="Boozoholics", is_group=True)

        slummy = Releaser.objects.create(name="Slummy", is_group=False)
        spb.member_memberships.create(member=slummy)
        bzh.member_memberships.create(member=slummy)

        with captured_stdout():
            call_command('match_janeway_sceners')

        self.assertTrue(
            slummy.external_links.filter(link_class='KestraBitworldAuthor', parameter='126').exists()
        )
