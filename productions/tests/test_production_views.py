# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from io import BytesIO
import json
import os

from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import patch
import PIL.Image

from demoscene.models import BlacklistedTag, Edit, Nick, Releaser
from demoscene.tests.utils import MediaTestMixin
from parties.models import Party
from platforms.models import Platform
from productions.models import Production, ProductionLink, ProductionType


def get_test_image():
    f = BytesIO()
    image = PIL.Image.new('RGBA', (200, 200), 'white')
    image.save(f, 'PNG')
    return ImageFile(f, name='test.png')


class TestIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        demo = ProductionType.objects.get(name='Demo').id
        zx = Platform.objects.get(name='ZX Spectrum').id

        pondlife = Production.objects.get(title='Pondlife')
        pondlife.screenshots.create(
            thumbnail_url='http://example.com/pondlife.thumb.png', thumbnail_width=130, thumbnail_height=100
        )

        response = self.client.get('/productions/?platform=%d&production_type=%d' % (zx, demo))
        self.assertEqual(response.status_code, 200)

    def test_get_by_title(self):
        response = self.client.get('/productions/?order=title')
        self.assertEqual(response.status_code, 200)

    def test_get_by_date_asc(self):
        response = self.client.get('/productions/?dir=asc')
        self.assertEqual(response.status_code, 200)


class TestTagIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.tags.add('48k')
        response = self.client.get('/productions/tagged/48k/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/productions/tagged/something-random/')
        self.assertEqual(response.status_code, 200)


class TestShowProduction(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.screenshots.create()
        pondlife.links.create(link_class='BaseUrl', parameter='http://example.com/pondlife.zip', is_download_link=True)
        pondlife.links.create(link_class='AmigascneFile', parameter='/demos/pondlife.zip', is_download_link=True)
        pondlife.links.create(link_class='PaduaOrgFile', parameter='/demos/pondlife.zip', is_download_link=True)
        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '/productions/%d/screenshots/edit/' % pondlife.id)

    def test_get_locked(self):
        mooncheese = Production.objects.get(title="Mooncheese")
        mooncheese.screenshots.create()
        response = self.client.get('/productions/%d/' % mooncheese.id)
        self.assertEqual(response.status_code, 200)

    def test_get_with_video(self):
        pondlife = Production.objects.get(title="Pondlife")

        # hack to stop ProductionLink.save from clearing embed details on link change
        pondlife.links.create(link_class='BaseUrl', parameter='http://example.com/pondlife.zip', is_download_link=False)
        pondlife.links.update(
            link_class='YoutubeVideo', parameter='1lFBXWxSrKE',
            thumbnail_url='http://example.com/yt.png', thumbnail_width=320, thumbnail_height=240
        )

        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_with_big_video(self):
        pondlife = Production.objects.get(title="Pondlife")

        # hack to stop ProductionLink.save from clearing embed details on link change
        pondlife.links.create(link_class='BaseUrl', parameter='http://example.com/pondlife.zip', is_download_link=False)
        pondlife.links.update(
            link_class='YoutubeVideo', parameter='1lFBXWxSrKE',
            thumbnail_url='http://example.com/yt.png', thumbnail_width=640, thumbnail_height=480
        )

        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_with_video_and_screenshot(self):
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.screenshots.create(
            original_url="http://example.com/orig.png",
            standard_url="http://example.com/standard.png",
            standard_width=400,
            standard_height=300,
        )

        # hack to stop ProductionLink.save from clearing embed details on link change
        pondlife.links.create(link_class='BaseUrl', parameter='http://example.com/pondlife.zip', is_download_link=False)
        pondlife.links.update(
            link_class='YoutubeVideo', parameter='1lFBXWxSrKE',
            thumbnail_url='http://example.com/yt.png', thumbnail_width=320, thumbnail_height=240
        )

        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_with_video_and_mosaic(self):
        pondlife = Production.objects.get(title="Pondlife")
        for i in range(0, 4):
            pondlife.screenshots.create(
                original_url="http://example.com/orig%d.png" % i,
                standard_url="http://example.com/standard%d.png" % i,
                standard_width=400,
                standard_height=300,
            )

        # hack to stop ProductionLink.save from clearing embed details on link change
        pondlife.links.create(link_class='BaseUrl', parameter='http://example.com/pondlife.zip', is_download_link=False)
        pondlife.links.update(
            link_class='YoutubeVideo', parameter='1lFBXWxSrKE',
            thumbnail_url='http://example.com/yt.png', thumbnail_width=320, thumbnail_height=240
        )

        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_with_mosaic(self):
        pondlife = Production.objects.get(title="Pondlife")
        for i in range(0, 4):
            pondlife.screenshots.create(
                original_url="http://example.com/orig%d.png" % i,
                standard_url="http://example.com/standard%d.png" % i,
                standard_width=400,
                standard_height=300,
            )
        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_as_admin(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')

        pondlife = Production.objects.get(title="Pondlife")
        pondlife.screenshots.create()
        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/productions/%d/screenshots/edit/' % pondlife.id)

    def test_get_pack(self):
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.types.add(ProductionType.objects.get(name='Pack'))
        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_non_prod(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/' % cybrev.id)
        self.assertRedirects(response, '/music/%d/' % cybrev.id)


class TestShowHistory(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/history/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_non_prod(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/history/' % cybrev.id)
        self.assertRedirects(response, '/music/%d/history/' % cybrev.id)


class TestCreateProduction(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/productions/new/')
        self.assertEqual(response.status_code, 200)

    def test_get_with_releaser_id(self):
        gasman = Releaser.objects.get(name='Gasman')
        response = self.client.get('/productions/new/?releaser_id=%d' % gasman.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gasman')

    def test_get_with_nonexistent_releaser_id(self):
        gasman = Releaser.objects.get(name='Gasman')
        response = self.client.get('/productions/new/?releaser_id=9999')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/new/', {
            'title': 'Ultraviolet',
            'byline_search': 'Gasman',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'release_date': 'march 2017',
            'type': ProductionType.objects.get(name='Demo').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/productions/%d/' % Production.objects.get(title='Ultraviolet').id)

    def test_post_empty_title(self):
        response = self.client.post('/productions/new/', {
            'title': '     ',
            'byline_search': 'Gasman',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'release_date': 'march 2017',
            'type': ProductionType.objects.get(name='Demo').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_post_with_unspaced_author_separators(self):
        response = self.client.post('/productions/new/', {
            'title': 'Ultraviolet',
            'byline_search': 'Gasman+Yerzmyey / Hooy-Program+Raww Arse',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'byline_author_match_1_id': Nick.objects.get(name='Yerzmyey').id,
            'byline_author_match_1_name': 'Yerzmyey',
            'byline_author_affiliation_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_affiliation_match_0_name': 'Hooy-Program',
            'byline_author_affiliation_match_1_id': Nick.objects.get(name='Raww Arse').id,
            'byline_author_affiliation_match_1_name': 'Raww Arse',
            'release_date': 'march 2017',
            'type': ProductionType.objects.get(name='Demo').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        ultraviolet = Production.objects.get(title='Ultraviolet')
        self.assertRedirects(response, '/productions/%d/' % ultraviolet.id)
        self.assertIn(Nick.objects.get(name='Yerzmyey'), ultraviolet.author_nicks.all())
        self.assertIn(Nick.objects.get(name='Hooy-Program'), ultraviolet.author_affiliation_nicks.all())

    def test_post_byline_explicit_lookup(self):
        response = self.client.post('/productions/new/', {
            'title': 'Ultraviolet',
            'byline_search': 'Gasman+Yerzmyey / Hooy-Program+Raww Arse',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'byline_author_match_1_id': Nick.objects.get(name='Yerzmyey').id,
            'byline_author_match_1_name': 'Yerzmyey',
            'byline_author_affiliation_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_affiliation_match_0_name': 'Hooy-Program',
            'byline_author_affiliation_match_1_id': Nick.objects.get(name='Raww Arse').id,
            'byline_author_affiliation_match_1_name': 'Raww Arse',
            'byline_lookup': 'Find names',
            'release_date': 'march 2017',
            'type': ProductionType.objects.get(name='Demo').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select the appropriate sceners / groups from the lists.")

    def test_post_unmatched_author_nick(self):
        response = self.client.post('/productions/new/', {
            'title': 'Ultraviolet',
            'byline_search': 'Gosman+Yorzmyey / Hooy-Program+Raww Arse',
            'release_date': 'march 2017',
            'type': ProductionType.objects.get(name='Demo').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not all names could be matched to a scener or group; please select the appropriate ones from the lists.")

    def test_post_unmatched_author_affiliation_nick(self):
        response = self.client.post('/productions/new/', {
            'title': 'Ultraviolet',
            'byline_search': 'Gasman+Yerzmyey / Hooy-Progrom+Raww Orse',
            'release_date': 'march 2017',
            'type': ProductionType.objects.get(name='Demo').id,
            'platform': Platform.objects.get(name='ZX Spectrum').id,
            'links-TOTAL_FORMS': 0,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not all names could be matched to a scener or group; please select the appropriate ones from the lists.")


class TestEditCoreDetails(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/edit_core_details/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get_production(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get('/productions/%d/edit_core_details/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_music(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/edit_core_details/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_get_graphics(self):
        skyrider = Production.objects.get(title="Skyrider")
        response = self.client.get('/productions/%d/edit_core_details/' % skyrider.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'Forever 2e3',
            'form-0-party_party_id': Party.objects.get(name='Forever 2e3').id,
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'P0ndlife')
        self.assertEqual(pondlife.invitation_parties.count(), 1)

        edit = Edit.for_model(pondlife, True).first()
        self.assertIn("Set title to 'P0ndlife'", edit.description)

        # no change => no edit log entry added
        edit_count = Edit.for_model(pondlife, True).count()

        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'Forever 2e3',
            'form-0-party_party_id': Party.objects.get(name='Forever 2e3').id,
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        edit = Edit.for_model(pondlife, True).first()
        self.assertEqual(edit_count, Edit.for_model(pondlife, True).count())

    def test_post_multiple_platforms(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'Pondlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': [
                Platform.objects.get(name='ZX Spectrum').id,
                Platform.objects.get(name='Commodore 64').id,
            ],
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        self.assertEqual(Production.objects.get(id=pondlife.id).platforms.count(), 2)

        edit = Edit.for_model(pondlife, True).first()
        self.assertIn(" platforms to ", edit.description)

    def test_post_unset_invitation(self):
        pondlife = Production.objects.get(title='Pondlife')
        forever2e3 = Party.objects.get(name='Forever 2e3')
        pondlife.invitation_parties.add(forever2e3)
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'Forever 2e3',
            'form-0-party_party_id': forever2e3.id,
            'form-0-DELETE': 'form-0-DELETE'
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'P0ndlife')
        self.assertEqual(pondlife.invitation_parties.count(), 0)

    def test_post_with_valid_party_lookup(self):
        # If the "Find party" button (visible without JS) is pressed, redisplay the form even if
        # the submission is valid
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'Forever 2e3',
            'form-0-party_party_id': '',
            'form-0-party_lookup': "Find party",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Party &#39;Forever 2e3&#39; found.")
        self.assertContains(
            response,
            '<input type="hidden" name="form-0-party_party_id" class="party_field_party_id" id="id_form-0-party" value="%d">' % Party.objects.get(name='Forever 2e3').id,
            html=True
        )
        self.assertContains(
            response,
            '<input type="text" name="title" required id="id_title" value="P0ndlife" maxlength="255">',
            html=True
        )

        # changes not committed yet
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'Pondlife')
        self.assertEqual(pondlife.invitation_parties.count(), 0)

    def test_post_with_unknown_party_lookup(self):
        # If the "Find party" button (visible without JS) is pressed, redisplay the form even if
        # the submission is valid
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'inerciademoparty 1963',
            'form-0-party_party_id': '',
            'form-0-party_lookup': "Find party",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No match found for &#39;inerciademoparty 1963&#39;")
        self.assertContains(
            response,
            '<input type="text" name="title" required id="id_title" value="P0ndlife" maxlength="255">',
            html=True
        )

        # changes not committed yet
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'Pondlife')
        self.assertEqual(pondlife.invitation_parties.count(), 0)

    def test_post_with_empty_party_lookup(self):
        # If the "Find party" button (visible without JS) is pressed, redisplay the form even if
        # the submission is valid
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': '',
            'form-0-party_party_id': '',
            'form-0-party_lookup': "Find party",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No party selected")
        self.assertContains(
            response,
            '<input type="text" name="title" required id="id_title" value="P0ndlife" maxlength="255">',
            html=True
        )

        # changes not committed yet
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'Pondlife')
        self.assertEqual(pondlife.invitation_parties.count(), 0)

    def test_post_with_bad_party_id_and_name(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'inerciademoparty 1963',
            'form-0-party_party_id': '9999',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No match found for &#39;inerciademoparty 1963&#39;")
        self.assertContains(
            response,
            '<input type="text" name="title" required id="id_title" value="P0ndlife" maxlength="255">',
            html=True
        )

        # changes not committed yet
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'Pondlife')
        self.assertEqual(pondlife.invitation_parties.count(), 0)

    def test_post_with_bad_party_id_but_good_name(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': ProductionType.objects.get(name='Demo').id,
            'platforms': Platform.objects.get(name='ZX Spectrum').id,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-party_search': 'forever 2e3',
            'form-0-party_party_id': '9999',
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        self.assertEqual(Production.objects.get(id=pondlife.id).title, 'P0ndlife')
        self.assertEqual(pondlife.invitation_parties.count(), 1)

    def test_set_type_and_platform(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'Pondlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': [
                ProductionType.objects.get(name='Intro').id,
                ProductionType.objects.get(name='Musicdisk').id,
            ],
            'platforms': Platform.objects.get(name='Commodore 64').id,
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        log_message = Edit.for_model(pondlife).first().description
        self.assertIn('types to Intro, Musicdisk', log_message)
        self.assertIn('platform to Commodore 64', log_message)

    def test_unset_type_and_platform(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'Pondlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        log_message = Edit.for_model(pondlife).first().description
        self.assertIn('type to none', log_message)
        self.assertIn('platform to none', log_message)

    def test_set_empty_title(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': '    ',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_set_empty_byline(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/edit_core_details/' % pondlife.id, {
            'title': 'Pondlife',
            'byline_search': '',
            'release_date': '18 March 2001',
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)

    def test_set_music_type_and_platform(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.post('/productions/%d/edit_core_details/' % cybrev.id, {
            'title': "Cybernoid's Revenge",
            'byline_search': 'Gasman',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'release_date': '18 March 2001',
            'type': ProductionType.objects.get(name='Streaming Music').id,
            'platforms': Platform.objects.get(name='Commodore 64').id,
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/music/%d/' % cybrev.id)
        log_message = Edit.for_model(cybrev).first().description
        self.assertIn('type to Streaming Music', log_message)
        self.assertIn('platform to Commodore 64', log_message)

    def test_set_music_without_initial_type(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        cybrev.types.clear()
        response = self.client.get('/productions/%d/edit_core_details/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_set_graphics_without_initial_type(self):
        skyrider = Production.objects.get(title="Skyrider")
        skyrider.types.clear()
        response = self.client.get('/productions/%d/edit_core_details/' % skyrider.id)
        self.assertEqual(response.status_code, 200)

    def test_set_graphics_type_and_platform(self):
        skyrider = Production.objects.get(title="Skyrider")
        response = self.client.post('/productions/%d/edit_core_details/' % skyrider.id, {
            'title': "Skyrider",
            'byline_search': 'Gasman',
            'byline_author_match_0_id': Nick.objects.get(name='Gasman').id,
            'byline_author_match_0_name': 'Gasman',
            'release_date': '18 March 2001',
            'type': ProductionType.objects.get(name='Photo').id,
            'platforms': Platform.objects.get(name='Commodore 64').id,
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        })
        self.assertRedirects(response, '/graphics/%d/' % skyrider.id)
        log_message = Edit.for_model(skyrider).first().description
        self.assertIn('type to Photo', log_message)
        self.assertIn('platform to Commodore 64', log_message)


class TestEditNotes(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/edit_notes/' % self.pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get(self):
        response = self.client.get('/productions/%d/edit_notes/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/edit_notes/' % self.pondlife.id, {
            'notes': "I am one thousand years old",
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(Production.objects.get(id=self.pondlife.id).notes, "I am one thousand years old")


class TestAddBlurb(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/add_blurb/' % self.pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get(self):
        response = self.client.get('/productions/%d/add_blurb/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/add_blurb/' % self.pondlife.id, {
            'body': "Hooy-Program's love letter to the humble duck",
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.blurbs.count(), 1)


class TestEditBlurb(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.blurb = self.pondlife.blurbs.create(body="Hooy-Program's love letter to the humble duck")

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/edit_blurb/%d/' % (self.pondlife.id, self.blurb.id))
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get(self):
        response = self.client.get('/productions/%d/edit_blurb/%d/' % (self.pondlife.id, self.blurb.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/edit_blurb/%d/' % (self.pondlife.id, self.blurb.id), {
            'body': "Hooy-Program's love letter to the humble mallard",
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.blurbs.get().body, "Hooy-Program's love letter to the humble mallard")


class TestDeleteBlurb(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.blurb = self.pondlife.blurbs.create(body="Hooy-Program's love letter to the humble duck")

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/delete_blurb/%d/' % (self.pondlife.id, self.blurb.id))
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get(self):
        response = self.client.get('/productions/%d/delete_blurb/%d/' % (self.pondlife.id, self.blurb.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/delete_blurb/%d/' % (self.pondlife.id, self.blurb.id), {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.blurbs.count(), 0)


class TestEditExternalLinks(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/edit_external_links/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/productions/%d/edit_external_links/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/edit_external_links/' % self.pondlife.id, {
            'links-TOTAL_FORMS': 1,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
            'links-0-url': 'https://www.pouet.net/prod.php?which=2611',
            'links-0-production': self.pondlife.id,
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(
            ProductionLink.objects.filter(production=self.pondlife, link_class='PouetProduction').count(),
            1
        )

    def test_post_download_link(self):
        response = self.client.post('/productions/%d/edit_external_links/' % self.pondlife.id, {
            'links-TOTAL_FORMS': 1,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
            'links-0-url': 'https://files.scene.org/get/parties/2001/forever01/spectrum/f2speccy.zip',
            'links-0-production': self.pondlife.id,
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertTrue(
            ProductionLink.objects.get(production=self.pondlife, link_class='SceneOrgFile').is_download_link
        )


class TestEditDownloadLinks(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/edit_download_links/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/productions/%d/edit_download_links/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/edit_download_links/' % self.pondlife.id, {
            'links-TOTAL_FORMS': 1,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
            'links-0-url': 'https://files.scene.org/get/parties/2001/forever01/spectrum/f2speccy.zip',
            'links-0-production': self.pondlife.id,
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(
            ProductionLink.objects.filter(production=self.pondlife, link_class='SceneOrgFile').count(),
            1
        )

    def test_post_unicode(self):
        response = self.client.post('/productions/%d/edit_download_links/' % self.pondlife.id, {
            'links-TOTAL_FORMS': 1,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
            'links-0-url': 'https://files.scene.org/get/parties/2001/forever01/spectrum/pöndlife.zip',
            'links-0-production': self.pondlife.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "URL must be pure ASCII - try copying it from your browser location bar")

    def test_post_external_link(self):
        response = self.client.post('/productions/%d/edit_download_links/' % self.pondlife.id, {
            'links-TOTAL_FORMS': 1,
            'links-INITIAL_FORMS': 0,
            'links-MIN_NUM_FORMS': 0,
            'links-MAX_NUM_FORMS': 1000,
            'links-0-url': 'https://www.pouet.net/prod.php?which=2611',
            'links-0-production': self.pondlife.id,
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertFalse(
            ProductionLink.objects.get(production=self.pondlife, link_class='PouetProduction').is_download_link
        )


class TestShowScreenshots(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/screenshots/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_music(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/screenshots/' % cybrev.id)
        self.assertRedirects(response, '/productions/%d/artwork/' % cybrev.id)


class TestShowArtwork(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/artwork/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_music(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/artwork/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/screenshots/' % pondlife.id)


class TestEditScreenshots(TestCase):
    fixtures = ['tests/gasman.json']

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', email='testuser@example.com', password='12345')
        self.client.login(username='testuser', password='12345')
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/screenshots/edit/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)

    def test_get(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/screenshots/edit/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_music(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/screenshots/edit/' % cybrev.id)
        self.assertRedirects(response, '/productions/%d/artwork/edit/' % cybrev.id)


class TestEditArtwork(TestCase):
    fixtures = ['tests/gasman.json']

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', email='testuser@example.com', password='12345')
        self.client.login(username='testuser', password='12345')
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/artwork/edit/' % cybrev.id)
        self.assertRedirects(response, '/music/%d/' % cybrev.id)

    def test_get(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/artwork/edit/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_nonmusic(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/artwork/edit/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/screenshots/edit/' % pondlife.id)


class TestAddScreenshot(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/add_screenshot/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get_production(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get('/productions/%d/add_screenshot/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_production(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get('/productions/%d/add_artwork/' % pondlife.id)
        self.assertRedirects(response, '/productions/%d/add_screenshot/' % pondlife.id)

    def test_get_music(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/add_artwork/' % cybrev.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_music(self):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.get('/productions/%d/add_screenshot/' % cybrev.id)
        self.assertRedirects(response, '/productions/%d/add_artwork/' % cybrev.id)

    @patch('screenshots.tasks.create_screenshot_versions_from_local_file')
    def test_post_production_single(self, create_screenshot_versions_from_local_file):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/add_screenshot/' % pondlife.id, {
            'screenshot': SimpleUploadedFile('test.png', get_test_image().file.getvalue()),
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        self.assertEqual(pondlife.screenshots.count(), 1)
        self.assertEqual(create_screenshot_versions_from_local_file.delay.call_count, 1)
        screenshot_id, filename = create_screenshot_versions_from_local_file.delay.call_args.args
        self.assertEqual(screenshot_id, pondlife.screenshots.get().id)
        os.remove(filename)

    @patch('screenshots.tasks.create_screenshot_versions_from_local_file')
    def test_post_production_multiple(self, create_screenshot_versions_from_local_file):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.post('/productions/%d/add_screenshot/' % pondlife.id, {
            'screenshot': [
                SimpleUploadedFile('test1.png', get_test_image().file.getvalue()),
                SimpleUploadedFile('test2.png', get_test_image().file.getvalue()),
            ],
        })
        self.assertRedirects(response, '/productions/%d/' % pondlife.id)
        self.assertEqual(pondlife.screenshots.count(), 2)
        self.assertEqual(create_screenshot_versions_from_local_file.delay.call_count, 2)
        for call in create_screenshot_versions_from_local_file.delay.call_args_list:
            _, filename = call.args
            os.remove(filename)

    @patch('screenshots.tasks.create_screenshot_versions_from_local_file')
    def test_post_music_single(self, create_screenshot_versions_from_local_file):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.post('/productions/%d/add_artwork/' % cybrev.id, {
            'screenshot': SimpleUploadedFile('test.png', get_test_image().file.getvalue()),
        })
        self.assertRedirects(response, '/music/%d/' % cybrev.id)
        self.assertEqual(cybrev.screenshots.count(), 1)
        self.assertEqual(create_screenshot_versions_from_local_file.delay.call_count, 1)
        screenshot_id, filename = create_screenshot_versions_from_local_file.delay.call_args.args
        self.assertEqual(screenshot_id, cybrev.screenshots.get().id)
        os.remove(filename)

    @patch('screenshots.tasks.create_screenshot_versions_from_local_file')
    def test_post_music_multiple(self, create_screenshot_versions_from_local_file):
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        response = self.client.post('/productions/%d/add_artwork/' % cybrev.id, {
            'screenshot': [
                SimpleUploadedFile('test1.png', get_test_image().file.getvalue()),
                SimpleUploadedFile('test2.png', get_test_image().file.getvalue()),
            ],
        })
        self.assertRedirects(response, '/music/%d/' % cybrev.id)
        self.assertEqual(cybrev.screenshots.count(), 2)
        self.assertEqual(create_screenshot_versions_from_local_file.delay.call_count, 2)
        for call in create_screenshot_versions_from_local_file.delay.call_args_list:
            _, filename = call.args
            os.remove(filename)


class TestDeleteScreenshot(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.pondlife_screenshot = self.pondlife.screenshots.create()
        self.cybrev = Production.objects.get(title="Cybernoid's Revenge")
        self.cybrev_artwork = self.cybrev.screenshots.create()

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/delete_screenshot/%d/' % (self.pondlife.id, self.pondlife_screenshot.id))
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get_production(self):
        response = self.client.get('/productions/%d/delete_screenshot/%d/' % (self.pondlife.id, self.pondlife_screenshot.id))
        self.assertEqual(response.status_code, 200)

    def test_redirect_production(self):
        response = self.client.get('/productions/%d/delete_artwork/%d/' % (self.pondlife.id, self.pondlife_screenshot.id))
        self.assertRedirects(response, '/productions/%d/delete_screenshot/%d/' % (self.pondlife.id, self.pondlife_screenshot.id))

    def test_get_music(self):
        response = self.client.get('/productions/%d/delete_artwork/%d/' % (self.cybrev.id, self.cybrev_artwork.id))
        self.assertEqual(response.status_code, 200)

    def test_redirect_music(self):
        response = self.client.get('/productions/%d/delete_screenshot/%d/' % (self.cybrev.id, self.cybrev_artwork.id))
        self.assertRedirects(response, '/productions/%d/delete_artwork/%d/' % (self.cybrev.id, self.cybrev_artwork.id))

    def test_post_production(self):
        response = self.client.post('/productions/%d/delete_screenshot/%d/' % (self.pondlife.id, self.pondlife_screenshot.id), {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/%d/screenshots/edit/' % self.pondlife.id)
        self.assertEqual(self.pondlife.screenshots.count(), 0)

    def test_post_music(self):
        response = self.client.post('/productions/%d/delete_artwork/%d/' % (self.cybrev.id, self.cybrev_artwork.id), {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/%d/artwork/edit/' % self.cybrev.id)
        self.assertEqual(self.cybrev.screenshots.count(), 0)


class TestAddCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/add_credit/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get('/productions/%d/add_credit/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_get_ajax(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get(
            '/productions/%d/add_credit/' % pondlife.id, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title='Pondlife')
        yerz = Nick.objects.get(name='Yerzmyey')

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': 'yerzmyey',
            'nick_match_id': yerz.id,
            'nick_match_name': 'yerzmyey',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 2',
        })
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % pondlife.id)
        self.assertEqual(1, pondlife.credits.filter(nick=yerz).count())

    def test_post_with_whitespace(self):
        pondlife = Production.objects.get(title='Pondlife')
        yerz = Nick.objects.get(name='Yerzmyey')

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': '  yerzmyey  ',
            'nick_match_id': yerz.id,
            'nick_match_name': 'yerzmyey',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 2',
        })
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % pondlife.id)
        self.assertEqual(1, pondlife.credits.filter(nick=yerz).count())

    def test_ambiguous_nick(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.author_nicks.clear()
        yerz = Nick.objects.get(name='Yerzmyey')
        # create fake Yerzmyey who isn't a member of Hooy-Program
        Releaser.objects.create(name='Yerzmyey', is_group=False)

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': 'yerzmyey',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 2',
        })
        # cannot match, as both Yerzmyeys are ranked equally
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select the appropriate nick from the list.")

    def test_prefer_group_member_when_matching(self):
        pondlife = Production.objects.get(title='Pondlife')
        yerz = Nick.objects.get(name='Yerzmyey')
        # create fake Yerzmyey who isn't a member of Hooy-Program
        Releaser.objects.create(name='Yerzmyey', is_group=False)

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': 'yerzmyey',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 2',
        })
        # real Yerzmyey is matched based on the production being authored by Hooy-Program
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % pondlife.id)
        self.assertEqual(1, pondlife.credits.filter(nick=yerz).count())

    def test_post_new_scener(self):
        pondlife = Production.objects.get(title='Pondlife')

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': 'Justinas',
            'nick_match_id': 'newscener',
            'nick_match_name': 'Justinas',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 5',
        })
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % pondlife.id)
        self.assertEqual(1, pondlife.credits.filter(nick__name='Justinas').count())
        self.assertFalse(Nick.objects.get(name='Justinas').releaser.is_group)

    def test_post_new_group(self):
        pondlife = Production.objects.get(title='Pondlife')

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': 'ZeroTeam',
            'nick_match_id': 'newgroup',
            'nick_match_name': 'ZeroTeam',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 5',
        })
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % pondlife.id)
        self.assertEqual(1, pondlife.credits.filter(nick__name='ZeroTeam').count())
        self.assertTrue(Nick.objects.get(name='ZeroTeam').releaser.is_group)

    def test_post_ajax(self):
        pondlife = Production.objects.get(title='Pondlife')
        yerz = Nick.objects.get(name='Yerzmyey')

        response = self.client.post('/productions/%d/add_credit/' % pondlife.id, {
            'nick_search': 'yerzmyey',
            'nick_match_id': yerz.id,
            'nick_match_name': 'yerzmyey',
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-id': '',
            'credit-0-category': 'Music',
            'credit-0-role': 'Part 2',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, pondlife.credits.filter(nick=yerz).count())


class TestEditCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.gasman = Nick.objects.get(name='Gasman')
        self.laesq = Nick.objects.get(name='LaesQ')
        self.pondlife_credit = self.pondlife.credits.get(nick=self.gasman)

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        mooncheese_credit = mooncheese.credits.create(nick=Nick.objects.get(name='Shingebis'), category='Code')
        response = self.client.get('/productions/%d/edit_credit/%d/' % (mooncheese.id, mooncheese_credit.id))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            '/productions/%d/edit_credit/%d/' % (self.pondlife.id, self.pondlife_credit.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_get_ajax(self):
        response = self.client.get(
            '/productions/%d/edit_credit/%d/' % (self.pondlife.id, self.pondlife_credit.id),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        pondlife = Production.objects.get(title='Pondlife')

        response = self.client.post(
            '/productions/%d/edit_credit/%d/' % (self.pondlife.id, self.pondlife_credit.id),
            {
                'nick_search': 'gasman',
                'nick_match_id': self.gasman.id,
                'nick_match_name': 'gasman',
                'credit-TOTAL_FORMS': 2,
                'credit-INITIAL_FORMS': 1,
                'credit-MIN_NUM_FORMS': 0,
                'credit-MAX_NUM_FORMS': 1000,
                'credit-0-id': self.pondlife_credit.id,
                'credit-0-category': 'Code',
                'credit-0-role': '',
                'credit-0-DELETE': 'credit-0-DELETE',
                'credit-1-id': '',
                'credit-1-category': 'Music',
                'credit-1-role': 'Part 1',
            }
        )
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % self.pondlife.id)
        self.assertEqual('Music', pondlife.credits.get(nick=self.gasman).category)

    def test_change_nick(self):
        pondlife = Production.objects.get(title='Pondlife')

        response = self.client.post(
            '/productions/%d/edit_credit/%d/' % (self.pondlife.id, self.pondlife_credit.id),
            {
                'nick_search': 'laesq',
                'nick_match_id': self.laesq.id,
                'nick_match_name': 'laesq',
                'credit-TOTAL_FORMS': 2,
                'credit-INITIAL_FORMS': 1,
                'credit-MIN_NUM_FORMS': 0,
                'credit-MAX_NUM_FORMS': 1000,
                'credit-0-id': self.pondlife_credit.id,
                'credit-0-category': 'Code',
                'credit-0-role': '',
                'credit-0-DELETE': 'credit-0-DELETE',
                'credit-1-id': '',
                'credit-1-category': 'Music',
                'credit-1-role': 'Part 1',
            }
        )
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % self.pondlife.id)
        self.assertEqual('Music', pondlife.credits.get(nick=self.laesq).category)


class TestDeleteCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.gasman = Nick.objects.get(name='Gasman')
        self.pondlife_credit = self.pondlife.credits.get(nick=self.gasman)

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        mooncheese_credit = mooncheese.credits.create(nick=Nick.objects.get(name='Shingebis'), category='Code')
        response = self.client.get('/productions/%d/delete_credit/%d/' % (mooncheese.id, mooncheese_credit.id))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            '/productions/%d/delete_credit/%d/' % (self.pondlife.id, self.pondlife_credit.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/delete_credit/%d/' % (self.pondlife.id, self.pondlife_credit.id), {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/%d/?editing=credits#credits_panel' % self.pondlife.id)
        self.assertEqual(self.pondlife.credits.count(), 0)


class TestEditSoundtracks(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/edit_soundtracks/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/productions/%d/edit_soundtracks/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        soundtrack_link = self.pondlife.soundtrack_links.get()
        response = self.client.post('/productions/%d/edit_soundtracks/' % self.pondlife.id, {
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-ORDER': 1,
            'form-0-id': soundtrack_link.id,
            'form-0-soundtrack_id': soundtrack_link.soundtrack_id,
            'form-0-DELETE': 'form-0-DELETE',
            'form-1-ORDER': 2,
            'form-1-id': '',
            'form-1-soundtrack_id': '',
            'form-1-soundtrack_title': 'Fantasia',
            'form-1-soundtrack_byline_search': '',
            'form-2-ORDER': 3,
            'form-2-id': '',
            'form-2-soundtrack_id': '',
            'form-2-soundtrack_title': '',
            'form-2-soundtrack_byline_search': '',
            'form-2-DELETE': 'form-2-DELETE',
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.soundtrack_links.count(), 1)
        self.assertEqual(self.pondlife.soundtrack_links.first().soundtrack.title, 'Fantasia')

        edit = Edit.for_model(self.pondlife, True).first()
        self.assertIn("Edited soundtrack details for Pondlife", edit.description)

    def test_post_with_empty(self):
        soundtrack_link = self.pondlife.soundtrack_links.get()
        response = self.client.post('/productions/%d/edit_soundtracks/' % self.pondlife.id, {
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-ORDER': 1,
            'form-0-id': soundtrack_link.id,
            'form-0-soundtrack_id': soundtrack_link.soundtrack_id,
            'form-0-DELETE': 'form-0-DELETE',
            'form-1-ORDER': 2,
            'form-1-id': '',
            'form-1-soundtrack_id': '',
            'form-1-soundtrack_title': 'Fantasia',
            'form-1-soundtrack_byline_search': '',
            'form-2-ORDER': 3,
            'form-2-id': '',
            'form-2-soundtrack_id': '',
            'form-2-soundtrack_title': '',
            'form-2-soundtrack_byline_search': '',
            'form-2-DELETE': 'form-2-DELETE',
            'form-3-id': '',
            'form-3-soundtrack_id': '',
            'form-3-soundtrack_title': '',
            'form-3-soundtrack_byline_search': '',
            'form-3-ORDER': 4,
        })
        # form is re-shown
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pondlife.soundtrack_links.count(), 1)
        self.assertEqual(self.pondlife.soundtrack_links.first().soundtrack.title, "Cybernoid's Revenge")


class TestEditPackContents(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.pondlife.types.add(ProductionType.objects.get(name='Pack'))
        self.madrielle = self.pondlife.pack_members.create(member=Production.objects.get(title='Madrielle'), position=1)

        self.mooncheese = Production.objects.get(title='Mooncheese')
        self.mooncheese.types.add(ProductionType.objects.get(name='Pack'))

    def test_locked(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        response = self.client.get('/productions/%d/edit_pack_contents/' % mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/productions/%d/edit_pack_contents/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/edit_pack_contents/' % self.pondlife.id, {
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-ORDER': 1,
            'form-0-id': self.madrielle.id,
            'form-0-member_id': self.madrielle.member_id,
            'form-0-DELETE': 'form-0-DELETE',
            'form-1-ORDER': 2,
            'form-1-id': '',
            'form-1-member_id': '',
            'form-1-member_title': 'Froob',
            'form-1-member_byline_search': '',
            'form-2-ORDER': 3,
            'form-2-id': '',
            'form-2-member_id': '',
            'form-2-member_title': '',
            'form-2-member_byline_search': '',
            'form-2-DELETE': 'form-2-DELETE',
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.pack_members.count(), 1)
        self.assertEqual(self.pondlife.pack_members.first().member.title, 'Froob')

    def test_post_with_empty(self):
        response = self.client.post('/productions/%d/edit_pack_contents/' % self.pondlife.id, {
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-ORDER': 1,
            'form-0-id': self.madrielle.id,
            'form-0-member_id': self.madrielle.member_id,
            'form-0-DELETE': 'form-0-DELETE',
            'form-1-ORDER': 2,
            'form-1-id': '',
            'form-1-member_id': '',
            'form-1-member_title': 'Froob',
            'form-1-member_byline_search': '',
            'form-2-ORDER': 3,
            'form-2-id': '',
            'form-2-member_id': '',
            'form-2-member_title': '',
            'form-2-member_byline_search': '',
            'form-2-DELETE': 'form-2-DELETE',
            'form-3-ORDER': 4,
            'form-3-id': '',
            'form-3-member_id': '',
            'form-3-member_title': '',
            'form-3-member_byline_search': '',
        })
        # form is re-shown
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pondlife.pack_members.count(), 1)
        self.assertEqual(self.pondlife.pack_members.first().member.title, 'Madrielle')

    def test_post_and_create_with_byline(self):
        response = self.client.post('/productions/%d/edit_pack_contents/' % self.pondlife.id, {
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-ORDER': 1,
            'form-0-id': self.madrielle.id,
            'form-0-member_id': self.madrielle.member_id,
            'form-0-DELETE': 'form-0-DELETE',
            'form-1-ORDER': 2,
            'form-1-id': '',
            'form-1-member_id': '',
            'form-1-member_title': 'Froob',
            'form-1-member_byline_search': 'Gasman / Hooy-Program',
            'form-2-ORDER': 3,
            'form-2-id': '',
            'form-2-member_id': '',
            'form-2-member_title': '',
            'form-2-member_byline_search': '',
            'form-2-DELETE': 'form-2-DELETE',
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.pack_members.count(), 1)
        froob = self.pondlife.pack_members.first().member
        self.assertEqual(froob.title, 'Froob')
        self.assertEqual(froob.author_nicks.first().name, 'Gasman')
        self.assertEqual(froob.author_affiliation_nicks.first().name, 'Hooy-Program')


class TestEditTags(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.mooncheese = Production.objects.get(title='Mooncheese')
        BlacklistedTag.objects.create(tag='48k', replacement='zx-spectrum-48k')

    def test_post(self):
        response = self.client.post('/productions/%d/edit_tags/' % self.pondlife.id, {
            'tags': "fish, ducks"
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.tags.count(), 2)

    def test_tag_replacement(self):
        response = self.client.post('/productions/%d/edit_tags/' % self.pondlife.id, {
            'tags': "fish, 48k"
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(self.pondlife.tags.count(), 2)
        self.assertTrue(self.pondlife.tags.filter(name='zx-spectrum-48k').exists())

    def test_post_locked(self):
        response = self.client.post('/productions/%d/edit_tags/' % self.mooncheese.id, {
            'tags': "wensleydale, stilton"
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.mooncheese.tags.count(), 0)


class TestAddTag(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.mooncheese = Production.objects.get(title='Mooncheese')
        BlacklistedTag.objects.create(tag='demo', message="Tagging things as demo is really stupid.")

    def test_post(self):
        response = self.client.post('/productions/%d/add_tag/' % self.pondlife.id, {
            'tag_name': "fish"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pondlife.tags.count(), 1)

    def test_post_blacklisted(self):
        response = self.client.post('/productions/%d/add_tag/' % self.pondlife.id, {
            'tag_name': "demo"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pondlife.tags.count(), 0)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['message'], "Tagging things as demo is really stupid.")

    def test_post_locked(self):
        response = self.client.post('/productions/%d/add_tag/' % self.mooncheese.id, {
            'tag_name': "wensleydale"
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.mooncheese.tags.count(), 0)


class TestRemoveTag(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.pondlife.tags.add('fish')
        self.mooncheese = Production.objects.get(title='Mooncheese')
        self.mooncheese.tags.add('wensleydale')

    def test_post(self):
        response = self.client.post('/productions/%d/remove_tag/' % self.pondlife.id, {
            'tag_name': "fish"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pondlife.tags.count(), 0)

    def test_post_locked(self):
        response = self.client.post('/productions/%d/remove_tag/' % self.mooncheese.id, {
            'tag_name': "wensleydale"
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.mooncheese.tags.count(), 1)


class TestAutocompleteTags(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.tags.add('fish')
        pondlife.tags.add('ducks')

    def test_get(self):
        response = self.client.get('/productions/autocomplete_tags/', {'term': 'fis'})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json, ['fish'])


class TestAutocomplete(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/productions/autocomplete/', {'term': 'cyberno', 'supertype': 'music'})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json[0]['title'], "Cybernoid's Revenge")


class TestDelete(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_non_superuser(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/delete/' % self.pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get(self):
        response = self.client.get('/productions/%d/delete/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/productions/%d/delete/' % self.pondlife.id, {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/')
        self.assertFalse(Production.objects.filter(title='Pondlife').exists())

    def test_cancel(self):
        response = self.client.post('/productions/%d/delete/' % self.pondlife.id, {
            'no': 'no'
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertTrue(Production.objects.filter(title='Pondlife').exists())


class TestLocking(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.mooncheese = Production.objects.get(title='Mooncheese')

    def test_not_superuser(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/lock/' % self.pondlife.id)
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)

    def test_get_lock(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/productions/%d/lock/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_post_lock(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/productions/%d/lock/' % self.pondlife.id, {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertTrue(Production.objects.get(title='Pondlife').locked)

    def test_get_protected_view(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/protected/' % self.mooncheese.id)
        self.assertEqual(response.status_code, 200)

    def test_post_unlock(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/productions/%d/protected/' % self.mooncheese.id, {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/productions/%d/' % self.mooncheese.id)
        self.assertFalse(Production.objects.get(title='Mooncheese').locked)

    def test_non_superuser_cannot_unlock(self):
        self.client.login(username='testuser', password='12345')
        self.client.post('/productions/%d/protected/' % self.mooncheese.id, {
            'yes': 'yes'
        })
        self.assertTrue(Production.objects.get(title='Mooncheese').locked)


class TestCarousel(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get('/productions/%d/carousel/' % pondlife.id)
        self.assertEqual(response.status_code, 200)


class TestEditInfoFiles(MediaTestMixin, TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.mooncheese = Production.objects.get(title='Mooncheese')

        self.info1 = self.pondlife.info_files.create(
            file=File(name="pondlife1.txt", file=BytesIO(b"First info file for Pondlife")),
            filename="pondlife1.txt", filesize=100, sha1="1234123412341234"
        )
        self.info2 = self.pondlife.info_files.create(
            file=File(name="pondlife2.txt", file=BytesIO(b"Second info file for Pondlife")),
            filename="pondlife2.txt", filesize=100, sha1="1234123412341234"
        )

    def test_get_locked(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/edit_info/' % self.mooncheese.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/edit_info/' % self.pondlife.id)
        self.assertEqual(response.status_code, 200)

    def test_add_one(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post('/productions/%d/edit_info/' % self.pondlife.id, {
            'info_file': SimpleUploadedFile('pondlife3.txt', b"Third info file", content_type="text/plain")
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(3, self.pondlife.info_files.count())

    def test_add_multiple(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post('/productions/%d/edit_info/' % self.pondlife.id, {
            'info_file': [
                SimpleUploadedFile('pondlife3.txt', b"Third info file", content_type="text/plain"),
                SimpleUploadedFile('pondlife4.txt', b"Fourth info file", content_type="text/plain"),
            ]
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(4, self.pondlife.info_files.count())

    def test_delete_one(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/productions/%d/edit_info/' % self.pondlife.id, {
            'info_files-TOTAL_FORMS': 2,
            'info_files-INITIAL_FORMS': 2,
            'info_files-MIN_NUM_FORMS': 0,
            'info_files-MAX_NUM_FORMS': 1000,
            'info_files-0-DELETE': 'info_files-0-DELETE',
            'info_files-0-id': self.info1.id,
            'info_files-0-production': self.pondlife.id,
            'info_files-1-id': self.info2.id,
            'info_files-1-production': self.pondlife.id,
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(1, self.pondlife.info_files.count())

    def test_delete_multiple(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/productions/%d/edit_info/' % self.pondlife.id, {
            'info_files-TOTAL_FORMS': 2,
            'info_files-INITIAL_FORMS': 2,
            'info_files-MIN_NUM_FORMS': 0,
            'info_files-MAX_NUM_FORMS': 1000,
            'info_files-0-DELETE': 'info_files-0-DELETE',
            'info_files-0-id': self.info1.id,
            'info_files-0-production': self.pondlife.id,
            'info_files-1-DELETE': 'info_files-1-DELETE',
            'info_files-1-id': self.info2.id,
            'info_files-1-production': self.pondlife.id,
        })
        self.assertRedirects(response, '/productions/%d/' % self.pondlife.id)
        self.assertEqual(0, self.pondlife.info_files.count())


class TestInfoFile(MediaTestMixin, TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.pondlife = Production.objects.get(title='Pondlife')
        self.info = self.pondlife.info_files.create(
            file=File(name="pondlife1.txt", file=BytesIO(b"First info file for Pondlife")),
            filename="pondlife1.txt", filesize=100, sha1="1234123412341234"
        )

    def test_get_without_login(self):
        url = '/productions/%d/info/%d/' % (self.pondlife.id, self.info.id)
        response = self.client.get(url)
        self.assertRedirects(response, '/account/login/?next=%s' % url)

    def test_get_with_login(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/info/%d/' % (self.pondlife.id, self.info.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First info file for Pondlife")
