from __future__ import absolute_import, unicode_literals

from io import BytesIO
import os

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import patch
import PIL.Image

from demoscene.models import Nick
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
        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)

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
        self.assertTrue(Production.objects.filter(title='P0ndlife').exists())
        self.assertEqual(pondlife.invitation_parties.count(), 1)

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
        self.assertTrue(Production.objects.filter(title='P0ndlife').exists())
        self.assertEqual(pondlife.invitation_parties.count(), 0)


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


class TestEdiDownloadLinks(TestCase):
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
