from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from parties.models import Party
from productions.models import Production
from sceneorg.models import Directory, File


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


class TestCompoFolderLink(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_post(self):
        forever2e3 = Party.objects.get(name='Forever 2e3')
        zx1k = forever2e3.competitions.get(name='ZX 1K Intro')
        response = self.client.post('/sceneorg/compofolders/link/', {
            'directory_id': Directory.objects.get(path='/parties/2000/forever00/zx_1k/').id,
            'competition_id': zx1k.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(zx1k.sceneorg_directories.filter(path='/parties/2000/forever00/zx_1k/').exists())


class TestCompoFolderUnLink(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_post(self):
        forever2e3 = Party.objects.get(name='Forever 2e3')
        zx1k = forever2e3.competitions.get(name='ZX 1K Intro')
        directory = Directory.objects.get(path='/parties/2000/forever00/zx_1k/')
        zx1k.sceneorg_directories.add(directory)

        response = self.client.post('/sceneorg/compofolders/unlink/', {
            'directory_id': directory.id,
            'competition_id': zx1k.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(zx1k.sceneorg_directories.filter(path='/parties/2000/forever00/zx_1k/').exists())


class TestCompoFoldersDone(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_post(self):
        forever2e3 = Party.objects.get(name='Forever 2e3')
        response = self.client.post('/sceneorg/compofolders/done/%d/' % forever2e3.id)
        self.assertRedirects(response, '/sceneorg/compofolders/')
        self.assertTrue(Party.objects.get(name='Forever 2e3').sceneorg_compofolders_done)


class TestCompoFoldersShowDirectory(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        directory = Directory.objects.get(path='/parties/2000/forever00/zx_1k/')
        response = self.client.get('/sceneorg/compofolders/directory/%d/' % directory.id)
        self.assertEqual(response.status_code, 200)


class TestCompoFoldersShowCompetition(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        forever2e3 = Party.objects.get(name='Forever 2e3')
        zx1k = forever2e3.competitions.get(name='ZX 1K Intro')
        response = self.client.get('/sceneorg/compofolders/competition/%d/' % zx1k.id)
        self.assertEqual(response.status_code, 200)


class TestCompoFiles(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        forever2e3 = Party.objects.get(name='Forever 2e3')
        zx1k = forever2e3.competitions.get(name='ZX 1K Intro')
        directory = Directory.objects.get(path='/parties/2000/forever00/zx_1k/')
        zx1k.sceneorg_directories.add(directory)

        response = self.client.get('/sceneorg/compofiles/')
        self.assertEqual(response.status_code, 200)


class TestCompoFileDirectory(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        forever2e3 = Party.objects.get(name='Forever 2e3')
        zx1k = forever2e3.competitions.get(name='ZX 1K Intro')
        directory = Directory.objects.get(path='/parties/2000/forever00/zx_1k/')
        zx1k.sceneorg_directories.add(directory)

        response = self.client.get('/sceneorg/compofiles/dir/%d/' % directory.id)
        self.assertEqual(response.status_code, 200)


class TestCompoFileLink(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_post(self):
        madrielle = Production.objects.get(title='Madrielle')
        response = self.client.post('/sceneorg/compofiles/link/', {
            'file_id': File.objects.get(path='/parties/2000/forever00/zx_1k/madrielle.zip').id,
            'production_id': madrielle.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(madrielle.download_links.filter(
            link_class='SceneOrgFile', parameter='/parties/2000/forever00/zx_1k/madrielle.zip'
        ).exists())


class TestCompoFileUnlink(TestCase):
    fixtures = ['tests/sceneorg.json', 'tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_post(self):
        madrielle = Production.objects.get(title='Madrielle')
        madrielle.links.create(
            is_download_link=True,
            link_class='SceneOrgFile', parameter='/parties/2000/forever00/zx_1k/madrielle.zip'
        )
        madrielle_file = File.objects.get(path='/parties/2000/forever00/zx_1k/madrielle.zip')

        response = self.client.post('/sceneorg/compofiles/unlink/', {
            'file_id': madrielle_file.id,
            'production_id': madrielle.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(madrielle.download_links.filter(
            link_class='SceneOrgFile', parameter='/parties/2000/forever00/zx_1k/madrielle.zip'
        ).exists())
