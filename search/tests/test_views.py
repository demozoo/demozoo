from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from taggit.models import Tag, TaggedItem

from demoscene.models import Nick, Releaser
from productions.models import Production


class TestSearch(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        gasman = Releaser.objects.get(name='Gasman')
        gasman.notes = "Gasman once made a demo called Pondlife."
        gasman.save()

        call_command('reindex')

        pondlife = Production.objects.get(title='Pondlife')
        pondlife.tags.add('fish')

        madrielle = Production.objects.get(title='Madrielle')
        TaggedItem.objects.create(content_object=madrielle, tag=Tag.objects.get(name='fish'))

    def test_get(self):
        response = self.client.get('/search/?q=pondlife')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "demo called <b>Pondlife</b>")

    def test_get_with_category(self):
        response = self.client.get('/search/?q=pondlife&category=production')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")
        self.assertNotContains(response, "demo called <b>Pondlife</b>")

    def test_get_with_tag(self):
        response = self.client.get('/search/?q=pondlife+[fish]')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")
        self.assertNotContains(response, "demo called <b>Pondlife</b>")

        response = self.client.get('/search/?q=madrielle+tagged:fish')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Madrielle")

    def test_admin_search(self):
        response = self.client.get('/search/?q=westcott')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gasman")

        self.user = User.objects.create_superuser(username='testuser', email='testuser@example.com', password='12345')
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/search/?q=westcott')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")

    def test_get_with_platform(self):
        response = self.client.get('/search/?q=pondlife+platform:"ZX+Spectrum"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")

        response = self.client.get('/search/?q=pondlife+platform:"Commodore 64"')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Pondlife")

    def test_get_with_author(self):
        response = self.client.get('/search/?q=pondlife+author:"Raww+Arse"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")

        response = self.client.get('/search/?q=pondlife+author:"Papaya+Dezign"')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Pondlife")

    def test_get_with_affiliation(self):
        response = self.client.get('/search/?q=gasman+of:"Raww+Arse"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")

        response = self.client.get('/search/?q=gasman+of:"Papaya+Dezign"')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gasman")

    def test_get_with_group(self):
        response = self.client.get('/search/?q=gasman+group:"Raww+Arse"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")
        response = self.client.get('/search/?q=pondlife+group:"Raww+Arse"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")

        response = self.client.get('/search/?q=gasman+group:"Papaya+Dezign"')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gasman")
        response = self.client.get('/search/?q=pondlife+group:"Papaya+Dezign"')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Pondlife")

    def test_get_with_year(self):
        response = self.client.get('/search/?q=pondlife+year:2001')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")

        response = self.client.get('/search/?q=pondlife+year:2002')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Pondlife")

    def test_get_with_invalid_year(self):
        response = self.client.get('/search/?q=pondlife+year:dot')
        self.assertEqual(response.status_code, 200)

    def test_get_with_unknown_filter(self):
        response = self.client.get('/search/?q=pondlife+xyz:xyz')
        self.assertEqual(response.status_code, 200)

    def test_get_with_releaser_type(self):
        response = self.client.get('/search/?q=gasman+type:releaser')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")

        response = self.client.get('/search/?q=madrielle+type:releaser')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Madrielle")

    def test_get_with_group_type(self):
        response = self.client.get('/search/?q=gasman+type:group')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gasman")

        response = self.client.get('/search/?q=hooy+type:group')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hooy-Program")

    def test_get_with_scener_type(self):
        response = self.client.get('/search/?q=gasman+type:scener')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")

        response = self.client.get('/search/?q=hooy+type:scener')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Hooy-Program")

    def test_get_with_party_type(self):
        response = self.client.get('/search/?q=gasman+type:party')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gasman")

        response = self.client.get('/search/?q=Forever+type:party')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forever 2e3")

    def test_get_with_prod_type(self):
        response = self.client.get('/search/?q=madrielle+type:"4K Intro"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Madrielle")

        response = self.client.get('/search/?q=pondlife+type:"4K Intro"')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Pondlife")

    def test_bad_page_number(self):
        response = self.client.get('/search/?q=pondlife&page=amigaaaa')
        self.assertEqual(response.status_code, 200)

    def test_out_of_range_page_number(self):
        response = self.client.get('/search/?q=pondlife&page=9999')
        self.assertEqual(response.status_code, 200)

    def test_invalid_search(self):
        response = self.client.get('/search/?q=')
        self.assertEqual(response.status_code, 200)


class TestLiveSearch(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.screenshots.create(thumbnail_url='http://example.com/pondlife.thumb.png')

        response = self.client.get('/search/live/?q=pondli')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pondlife")

    def test_get_music(self):
        response = self.client.get('/search/live/?q=cybern&category=music')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cybernoid's Revenge")

    def test_get_scener(self):
        response = self.client.get('/search/live/?q=gasm&category=scener')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gasman")

    def test_get_group(self):
        hprg = Nick.objects.get(name='Hooy-Program')
        hprg.differentiator = 'ZX'
        hprg.save()
        response = self.client.get('/search/live/?q=hooy&category=group')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hooy-Program")

    def test_get_party(self):
        response = self.client.get('/search/live/?q=forev&category=party')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forever 2e3")

    def test_no_query(self):
        response = self.client.get('/search/live/')
        self.assertEqual(response.status_code, 200)
