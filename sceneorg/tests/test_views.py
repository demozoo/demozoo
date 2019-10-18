from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from parties.models import Party


class TestCompoFolders(TestCase):
    fixtures = ['tests/sceneorg.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/sceneorg/compofolders/')
        self.assertEqual(response.status_code, 200)

    def test_get_by_series(self):
        response = self.client.get('/sceneorg/compofolders/?order=series')
        self.assertEqual(response.status_code, 200)


class TestCompoFolderParty(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.forever2e3 = Party.objects.get(name='Forever 2e3')
        self.forever2e3.external_links.create(link_class='SceneOrgFolder', parameter='/parties/2000/forever00/')
        self.forever2e3.external_links.create(link_class='SceneOrgFolder', parameter='/parties/2000/forever00b/')

    def test_get(self):
        response = self.client.get('/sceneorg/compofolders/party/%d/' % self.forever2e3.id)
        self.assertEqual(response.status_code, 200)
