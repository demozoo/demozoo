from __future__ import absolute_import, unicode_literals

import datetime
import os.path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from mock import patch

from demoscene.models import Releaser
from maintenance.models import Exclusion
from mirror.models import ArchiveMember, Download, DownloadBlob
from parties.models import Party
from productions.models import Production, ProductionLink
from sceneorg.models import Directory


class TestReports(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')

    def test_index(self):
        response = self.client.get('/maintenance/')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_screenshots(self):
        response = self.client.get('/maintenance/prods_without_screenshots')
        self.assertEqual(response.status_code, 200)

        # test with invalid filter form
        response = self.client.get('/maintenance/prods_without_screenshots?platform=999')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_videos(self):
        response = self.client.get('/maintenance/prods_without_videos')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_credits(self):
        response = self.client.get('/maintenance/prods_without_credits')
        self.assertEqual(response.status_code, 200)

    def test_tracked_music_without_playable_links(self):
        response = self.client.get('/maintenance/tracked_music_without_playable_links')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_external_links(self):
        response = self.client.get('/maintenance/prods_without_external_links')
        self.assertEqual(response.status_code, 200)

    def test_staff_only_report(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/maintenance/prods_without_external_links')
        self.assertRedirects(response, '/')

    def test_prods_without_release_date(self):
        response = self.client.get('/maintenance/prods_without_release_date')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_dead_amigascne_links(self):
        response = self.client.get('/maintenance/prods_with_dead_amigascne_links')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_dead_amiga_nvg_org_links(self):
        response = self.client.get('/maintenance/prods_with_dead_amiga_nvg_org_links')
        self.assertEqual(response.status_code, 200)

    def test_sceneorg_download_links_with_unicode(self):
        response = self.client.get('/maintenance/sceneorg_download_links_with_unicode')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_platforms(self):
        response = self.client.get('/maintenance/prods_without_platforms')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_platforms_excluding_lost(self):
        response = self.client.get('/maintenance/prods_without_platforms_excluding_lost')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_platforms_with_downloads(self):
        response = self.client.get('/maintenance/prods_without_platforms_with_downloads')
        self.assertEqual(response.status_code, 200)

    def test_prods_without_release_date_with_placement(self):
        Production.objects.filter(title="Madrielle").update(release_date_date=None, release_date_precision='')
        response = self.client.get('/maintenance/prods_without_release_date_with_placement')
        self.assertEqual(response.status_code, 200)

    def test_prod_soundtracks_without_release_date(self):
        Production.objects.filter(title="Cybernoid's Revenge").update(release_date_date=None, release_date_precision='')
        response = self.client.get('/maintenance/prod_soundtracks_without_release_date')
        self.assertEqual(response.status_code, 200)

    def test_group_nicks_with_brackets(self):
        response = self.client.get('/maintenance/group_nicks_with_brackets')
        self.assertEqual(response.status_code, 200)

    def test_ambiguous_groups_with_no_differentiators(self):
        response = self.client.get('/maintenance/ambiguous_groups_with_no_differentiators')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_release_date_outside_party(self):
        Production.objects.filter(title="Madrielle").update(
            release_date_date=datetime.date(2001, 1, 1), release_date_precision='d'
        )
        response = self.client.get('/maintenance/prods_with_release_date_outside_party')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_same_named_credits(self):
        response = self.client.get('/maintenance/prods_with_same_named_credits')
        self.assertEqual(response.status_code, 200)

    def test_same_named_prods_by_same_releaser(self):
        response = self.client.get('/maintenance/same_named_prods_by_same_releaser')
        self.assertEqual(response.status_code, 200)

    def test_same_named_prods_without_special_chars(self):
        response = self.client.get('/maintenance/same_named_prods_without_special_chars')
        self.assertEqual(response.status_code, 200)

    def test_duplicate_external_links(self):
        Production.objects.get(title='Pondlife').links.create(link_class='PouetProduction', parameter='123')
        Production.objects.get(title='Madrielle').links.create(link_class='PouetProduction', parameter='123')

        Releaser.objects.get(name='Gasman').external_links.create(link_class='PouetGroup', parameter='123')
        Releaser.objects.get(name='Raww Arse').external_links.create(link_class='PouetGroup', parameter='123')
        response = self.client.get('/maintenance/duplicate_external_links')
        self.assertEqual(response.status_code, 200)

    def test_duplicate_releaser_kestra_links(self):
        response = self.client.get('/maintenance/duplicate_releaser_kestra_links')
        self.assertEqual(response.status_code, 200)

    def test_matching_real_names(self):
        response = self.client.get('/maintenance/matching_real_names')
        self.assertEqual(response.status_code, 200)

    def test_matching_surnames(self):
        response = self.client.get('/maintenance/matching_surnames')
        self.assertEqual(response.status_code, 200)

    def test_implied_memberships(self):
        response = self.client.get('/maintenance/implied_memberships')
        self.assertEqual(response.status_code, 200)

    def test_groups_with_same_named_members(self):
        response = self.client.get('/maintenance/groups_with_same_named_members')
        self.assertEqual(response.status_code, 200)

    def test_releasers_with_same_named_groups(self):
        response = self.client.get('/maintenance/releasers_with_same_named_groups')
        self.assertEqual(response.status_code, 200)

    def test_sceneorg_party_dirs_with_no_party(self):
        Directory.objects.create(path='/parties/', last_seen_at=datetime.datetime(2019, 1, 1))
        response = self.client.get('/maintenance/sceneorg_party_dirs_with_no_party')
        self.assertEqual(response.status_code, 200)

    def test_parties_with_incomplete_dates(self):
        response = self.client.get('/maintenance/parties_with_incomplete_dates')
        self.assertEqual(response.status_code, 200)

    def test_parties_with_no_location(self):
        response = self.client.get('/maintenance/parties_with_no_location')
        self.assertEqual(response.status_code, 200)

    def test_empty_releasers(self):
        response = self.client.get('/maintenance/empty_releasers')
        self.assertEqual(response.status_code, 200)

    def test_empty_competitions(self):
        response = self.client.get('/maintenance/empty_competitions')
        self.assertEqual(response.status_code, 200)

    def test_unresolved_screenshots(self):
        Production.objects.get(title='Pondlife').links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife.zip',
            is_download_link=True, is_unresolved_for_screenshotting=True
        )
        response = self.client.get('/maintenance/unresolved_screenshots')
        self.assertEqual(response.status_code, 200)

    def test_public_real_names(self):
        response = self.client.get('/maintenance/public_real_names')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/maintenance/public_real_names?without_note=1')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_blurbs(self):
        response = self.client.get('/maintenance/prods_with_blurbs')
        self.assertEqual(response.status_code, 200)

    def test_prod_comments(self):
        response = self.client.get('/maintenance/prod_comments')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/maintenance/prod_comments?page=amigaaaa')
        self.assertEqual(response.status_code, 200)

    def test_credits_to_move_to_text(self):
        response = self.client.get('/maintenance/credits_to_move_to_text')
        self.assertEqual(response.status_code, 200)

    def test_results_with_no_encoding(self):
        response = self.client.get('/maintenance/results_with_no_encoding')
        self.assertEqual(response.status_code, 200)

    def test_tiny_intros_without_download_links(self):
        response = self.client.get('/maintenance/tiny_intros_without_download_links')
        self.assertEqual(response.status_code, 200)

    def test_janeway_unique_author_name_matches(self):
        response = self.client.get('/maintenance/janeway_unique_author_name_matches')
        self.assertEqual(response.status_code, 200)

    def test_fix_release_dates_nonadmin(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        madrielle = Production.objects.get(title='Madrielle')
        response = self.client.post('/maintenance/fix_release_dates', {
            'production_id': madrielle.id,
            ('production_%d_release_date_date' % madrielle.id): '2000-01-01',
            ('production_%d_release_date_precision' % madrielle.id): 'd',
            'return_to': '/maintenance/',
        })
        self.assertRedirects(response, '/')

    def test_fix_release_dates(self):
        madrielle = Production.objects.get(title='Madrielle')
        response = self.client.post('/maintenance/fix_release_dates', {
            'production_id': madrielle.id,
            ('production_%d_release_date_date' % madrielle.id): '2000-01-01',
            ('production_%d_release_date_precision' % madrielle.id): 'd',
            'return_to': '/maintenance/',
        })
        self.assertRedirects(response, '/maintenance/')
        self.assertEqual(
            Production.objects.get(title='Madrielle').release_date_date,
            datetime.date(2000, 1, 1)
        )

    def test_exclude_nonadmin(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        response = self.client.post('/maintenance/exclude', {
            'report_name': 'streets_with_no_names',
            'record_id': 22
        })
        self.assertRedirects(response, '/')
        self.assertFalse(Exclusion.objects.filter(report_name='streets_with_no_names').exists())

    def test_exclude(self):
        response = self.client.post('/maintenance/exclude', {
            'report_name': 'streets_with_no_names',
            'record_id': 22
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Exclusion.objects.filter(report_name='streets_with_no_names').exists())

    def test_add_membership_nonadmin(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        gasman = Releaser.objects.get(name='Gasman')
        papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

        response = self.client.post('/maintenance/add_membership', {
            'member_id': gasman.id,
            'group_id': papaya_dezign.id
        })
        self.assertRedirects(response, '/')
        self.assertFalse(gasman.group_memberships.filter(group=papaya_dezign).exists())

    def test_add_membership(self):
        gasman = Releaser.objects.get(name='Gasman')
        papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

        response = self.client.post('/maintenance/add_membership', {
            'member_id': gasman.id,
            'group_id': papaya_dezign.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(gasman.group_memberships.filter(group=papaya_dezign).exists())

    def test_add_sceneorg_party_link_nonadmin(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        forever = Party.objects.get(name='Forever 2e3')

        response = self.client.post('/maintenance/add_sceneorg_link_to_party', {
            'party_id': forever.id,
            'path': '/parties/2000/forever2000/'
        })
        self.assertRedirects(response, '/')
        self.assertFalse(forever.external_links.filter(link_class='SceneOrgFolder').exists())

    def test_add_sceneorg_party_link(self):
        forever = Party.objects.get(name='Forever 2e3')

        response = self.client.post('/maintenance/add_sceneorg_link_to_party', {
            'party_id': forever.id,
            'path': '/parties/2000/forever2000/'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(forever.external_links.filter(link_class='SceneOrgFolder').exists())

    @patch('maintenance.views.create_screenshot_from_production_link')
    def test_resolve_screenshot_nonadmin(self, create_screenshot_from_production_link):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        pondlife_link = Production.objects.get(title='Pondlife').links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife.zip',
            is_download_link=True, is_unresolved_for_screenshotting=True
        )
        archive_member = ArchiveMember.objects.create(
            archive_sha1='123123123', filename='screenshot.png', file_size=6912
        )
        response = self.client.post('/maintenance/resolve_screenshot/%d/%d/' % (pondlife_link.id, archive_member.id), {'1': 1})
        self.assertRedirects(response, '/')
        self.assertTrue(ProductionLink.objects.get(id=pondlife_link.id).is_unresolved_for_screenshotting)
        self.assertFalse(create_screenshot_from_production_link.delay.called)

    @patch('maintenance.views.create_screenshot_from_production_link')
    def test_resolve_screenshot(self, create_screenshot_from_production_link):
        pondlife_link = Production.objects.get(title='Pondlife').links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife.zip',
            is_download_link=True, is_unresolved_for_screenshotting=True
        )
        archive_member = ArchiveMember.objects.create(
            archive_sha1='123123123', filename='screenshot.png', file_size=6912
        )
        response = self.client.post('/maintenance/resolve_screenshot/%d/%d/' % (pondlife_link.id, archive_member.id), {'1': 1})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProductionLink.objects.get(id=pondlife_link.id).is_unresolved_for_screenshotting)
        self.assertTrue(create_screenshot_from_production_link.delay.called)

    @patch('mirror.models.Download.fetch_from_s3')
    def test_view_archive_member(self, fetch_from_s3):
        Download.objects.create(
            downloaded_at=datetime.datetime.now(), sha1='1234123412341234', mirror_s3_key='test.zip'
        )
        archive_member = ArchiveMember.objects.create(
            archive_sha1='1234123412341234', filename='happycat.jpg', file_size=6617
        )

        with open(os.path.join(settings.FILEROOT, 'maintenance', 'fixtures', 'test.zip')) as f:
            fetch_from_s3.return_value = DownloadBlob('test.zip', f.read())

        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/maintenance/archive_member/%d/' % (archive_member.id))
        self.assertRedirects(response, '/')

        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/maintenance/archive_member/%d/' % (archive_member.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(len(response.content), 6617)
