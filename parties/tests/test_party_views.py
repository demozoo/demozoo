# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from io import BytesIO

from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

import PIL.Image

from demoscene.models import Edit
from demoscene.tests.utils import MediaTestMixin
from parties.models import Competition, Party, PartyExternalLink, PartySeries, ResultsFile
from productions.models import Production


class TestShowIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/parties/')
        self.assertEqual(response.status_code, 200)


class TestShowPartiesByDate(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/parties/by_date/')
        self.assertEqual(response.status_code, 200)


class TestShowParty(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        party = Party.objects.get(name='Forever 2e3')
        response = self.client.get('/parties/%d/' % party.id)
        self.assertEqual(response.status_code, 200)


class TestShowPartyHistory(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        party = Party.objects.get(name='Forever 2e3')
        response = self.client.get('/parties/%d/history/' % party.id)
        self.assertEqual(response.status_code, 200)


class TestShowPartySeries(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        party_series = PartySeries.objects.get(name='Forever')

        madrielle = Production.objects.get(title='Madrielle')
        madrielle.screenshots.create(
            thumbnail_url='http://example.com/madrielle.thumb.png', thumbnail_width=130, thumbnail_height=100,
            standard_url='http://example.com/madrielle.standard.png', standard_width=320, standard_height=240
        )

        response = self.client.get('/parties/series/%d/' % party_series.id)
        self.assertEqual(response.status_code, 200)


class TestShowPartySeriesHistory(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        party_series = PartySeries.objects.get(name='Forever')
        response = self.client.get('/parties/series/%d/history/' % party_series.id)
        self.assertEqual(response.status_code, 200)


class TestCreateParty(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/parties/new/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/new/', {
            'name': 'Revision 2011',
            'start_date': '22 april 2011',
            'end_date': '25 april 2011',
            'party_series_name': 'Revision'
        })
        self.assertRedirects(response, '/parties/%d/' % Party.objects.get(name='Revision 2011').id)

    def test_post_ajax(self):
        response = self.client.post('/parties/new/', {
            'name': 'Revision 2011',
            'start_date': '22 april 2011',
            'end_date': '25 april 2011',
            'party_series_name': 'Revision'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Party.objects.filter(name='Revision 2011').exists())


class TestEditParty(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_get(self):
        response = self.client.get('/parties/%d/edit/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/%d/edit/' % self.party.id, {
            'name': 'Forever 2000',
            'start_date': '17 march 2000',
            'end_date': '19 march 2000',
            'party_series_name': 'Forever',
            'website': 'http://forever.zeroteam.sk/',
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(Party.objects.get(id=self.party.id).name, "Forever 2000")
        self.assertEqual(PartySeries.objects.get(name='Forever').website, 'http://forever.zeroteam.sk/')

        edit = Edit.for_model(self.party, True).first()
        self.assertIn("Set name to 'Forever 2000'", edit.description)

        # no change => no edit log entry added
        edit_count = Edit.for_model(self.party, True).count()

        response = self.client.post('/parties/%d/edit/' % self.party.id, {
            'name': 'Forever 2000',
            'start_date': '17 march 2000',
            'end_date': '19 march 2000',
            'party_series_name': 'Forever',
            'website': 'http://forever.zeroteam.sk/',
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(edit_count, Edit.for_model(self.party, True).count())


class TestEditNotes(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/parties/%d/edit_notes/' % self.party.id)
        self.assertRedirects(response, '/parties/%d/' % self.party.id)

    def test_get(self):
        response = self.client.get('/parties/%d/edit_notes/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/%d/edit_notes/' % self.party.id, {
            'notes': "doo doo doo do do doo",
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(Party.objects.get(id=self.party.id).notes, "doo doo doo do do doo")


class TestEditExternalLinks(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_get(self):
        response = self.client.get('/parties/%d/edit_external_links/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/%d/edit_external_links/' % self.party.id, {
            'external_links-TOTAL_FORMS': 1,
            'external_links-INITIAL_FORMS': 0,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-url': 'https://twitter.com/forever8party',
            'external_links-0-party': self.party.id,
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(
            PartyExternalLink.objects.filter(party=self.party, link_class='TwitterAccount').count(),
            1
        )
        self.assertEqual(PartySeries.objects.get(name='Forever').twitter_username, 'forever8party')

    def test_post_with_pouet_link(self):
        response = self.client.post('/parties/%d/edit_external_links/' % self.party.id, {
            'external_links-TOTAL_FORMS': 2,
            'external_links-INITIAL_FORMS': 0,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-url': 'https://twitter.com/forever8party',
            'external_links-0-party': self.party.id,
            'external_links-1-url': 'https://www.pouet.net/party.php?which=181&when=2000',
            'external_links-1-party': self.party.id,
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(
            PartyExternalLink.objects.filter(party=self.party, link_class='TwitterAccount').count(),
            1
        )
        self.assertEqual(
            PartyExternalLink.objects.filter(party=self.party, link_class='PouetParty').count(),
            1
        )
        self.assertEqual(PartySeries.objects.get(name='Forever').twitter_username, 'forever8party')
        self.assertEqual(PartySeries.objects.get(name='Forever').pouet_party_id, 181)


class TestEditSeriesNotes(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.party_series = PartySeries.objects.get(name='Forever')

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/parties/series/%d/edit_notes/' % self.party_series.id)
        self.assertRedirects(response, '/parties/series/%d/' % self.party_series.id)

    def test_get(self):
        response = self.client.get('/parties/series/%d/edit_notes/' % self.party_series.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/series/%d/edit_notes/' % self.party_series.id, {
            'notes': "doo doo doo do do doo",
        })
        self.assertRedirects(response, '/parties/series/%d/' % self.party_series.id)
        self.assertEqual(PartySeries.objects.get(id=self.party_series.id).notes, "doo doo doo do do doo")


class TestEditSeries(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.party_series = PartySeries.objects.get(name='Forever')

    def test_get(self):
        response = self.client.get('/parties/series/%d/edit/' % self.party_series.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/series/%d/edit/' % self.party_series.id, {
            'name': "Forever",
            'website': 'http://forever.zeroteam.sk/',
        })
        self.assertRedirects(response, '/parties/series/%d/' % self.party_series.id)
        self.assertEqual(PartySeries.objects.get(id=self.party_series.id).website, 'http://forever.zeroteam.sk/')


class TestAddCompetition(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_get(self):
        response = self.client.get('/parties/%d/add_competition/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/parties/%d/add_competition/' % self.party.id, {
            'name': 'ZX Graphics',
            'shown_date': '18 march 2000',
        })
        self.assertRedirects(
            response,
            '/competitions/%d/edit' % Competition.objects.get(party__name="Forever 2e3", name="ZX Graphics").id
        )


class TestShowResultsFile(MediaTestMixin, TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        party = Party.objects.get(name="Forever 2e3")
        results_file = ResultsFile.objects.create(
            party=party,
            file=File(
                name="forever2e3.txt",
                file=BytesIO(b"You get a car! You get a car! Everybody gets a car!")
            ),
            filename="forever2e3.txt", filesize=100, sha1="1234123412341234"
        )

        response = self.client.get('/parties/%d/results_file/%d/' % (party.id, results_file.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You get a car! You get a car! Everybody gets a car!")

    def test_get_with_unknown_encoding(self):
        party = Party.objects.get(name="Forever 2e3")
        results_file = ResultsFile.objects.create(
            party=party,
            file=File(
                name="forever2e3.txt",
                file=BytesIO(b"You get a c\xe5r! You get a c\xe5r! Everybody gets a c\xe5r!")
            ),
            filename="forever2e3.txt", filesize=100, sha1="1234123412341234"
        )

        response = self.client.get('/parties/%d/results_file/%d/' % (party.id, results_file.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"You get a cår! You get a cår! Everybody gets a cår!")


class TestAutocomplete(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/parties/autocomplete/?term=forev')
        self.assertEqual(response.status_code, 200)


class TestEditInvitations(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_get(self):
        response = self.client.get('/parties/%d/edit_invitations/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/parties/%d/edit_invitations/' % self.party.id, {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-production_id': pondlife.id,
            'form-0-production_title': 'Pondlife',
            'form-0-production_byline_search': ''
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(self.party.invitations.count(), 1)

        edit = Edit.for_model(self.party, True).first()
        self.assertEqual("Set invitations to Pondlife", edit.description)

        # no change => no edit log entry added
        edit_count = Edit.for_model(self.party, True).count()
        response = self.client.post('/parties/%d/edit_invitations/' % self.party.id, {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-production_id': pondlife.id,
            'form-0-production_title': 'Pondlife',
            'form-0-production_byline_search': ''
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(edit_count, Edit.for_model(self.party, True).count())


class TestEditReleases(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_get(self):
        response = self.client.get('/parties/%d/edit_releases/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/parties/%d/edit_releases/' % self.party.id, {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-production_id': pondlife.id,
            'form-0-production_title': 'Pondlife',
            'form-0-production_byline_search': ''
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertEqual(self.party.releases.count(), 1)


class TestEditCompetition(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        party = Party.objects.get(name='Forever 2e3')
        competition = Competition.objects.get(party=party, name="ZX 1K Intro")
        response = self.client.get('/parties/%d/edit_competition/%d/' % (party.id, competition.id))
        self.assertRedirects(response, '/competitions/%d/edit' % competition.id)


class TestEditShareImage(MediaTestMixin, TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.party = Party.objects.get(name='Forever 2e3')

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/parties/%d/edit_share_image/' % self.party.id)
        self.assertRedirects(response, '/')

    def test_get(self):
        response = self.client.get('/parties/%d/edit_share_image/' % self.party.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        f = BytesIO()
        image = PIL.Image.new('RGBA', (200, 200), 'white')
        image.save(f, 'PNG')
        image_file = ImageFile(f, name='test.png')

        response = self.client.post('/parties/%d/edit_share_image/' % self.party.id, {
            'share_image_file': SimpleUploadedFile('test.png', image_file.file.getvalue())
        })
        self.assertRedirects(response, '/parties/%d/' % self.party.id)
        self.assertTrue(Party.objects.get(id=self.party.id).share_image_file.name)
        Party.objects.get(id=self.party.id).share_image_file.delete()
