from __future__ import absolute_import, unicode_literals

import datetime

from django.contrib.auth.models import User
from django.test import TestCase

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
        response = self.client.get('/maintenance/prods_without_release_date_with_placement')
        self.assertEqual(response.status_code, 200)

    def test_prod_soundtracks_without_release_date(self):
        response = self.client.get('/maintenance/prod_soundtracks_without_release_date')
        self.assertEqual(response.status_code, 200)

    def test_group_nicks_with_brackets(self):
        response = self.client.get('/maintenance/group_nicks_with_brackets')
        self.assertEqual(response.status_code, 200)

    def test_ambiguous_groups_with_no_differentiators(self):
        response = self.client.get('/maintenance/ambiguous_groups_with_no_differentiators')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_release_date_outside_party(self):
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
        response = self.client.get('/maintenance/unresolved_screenshots')
        self.assertEqual(response.status_code, 200)

    def test_public_real_names(self):
        response = self.client.get('/maintenance/public_real_names')
        self.assertEqual(response.status_code, 200)

    def test_prods_with_blurbs(self):
        response = self.client.get('/maintenance/prods_with_blurbs')
        self.assertEqual(response.status_code, 200)

    def test_prod_comments(self):
        response = self.client.get('/maintenance/prod_comments')
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
