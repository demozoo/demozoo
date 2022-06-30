from django.test import TestCase

from productions.cowbell import identify_link_as_track
from productions.models import Production


class TestCowbell(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.cybrev = Production.objects.get(title="Cybernoid's Revenge")

    def test_sceneorg_streaming(self):
        link = self.cybrev.links.create(
            link_class='SceneOrgFile',
            parameter='/music/groups/8bitpeoples/8bp043-08-gasman-norwegian_blue.mp3',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'mp3')
        self.assertEqual(
            url, 'https://archive.scene.org/pub/music/groups/8bitpeoples/8bp043-08-gasman-norwegian_blue.mp3'
        )

    def test_modland_mod(self):
        link = self.cybrev.links.create(
            link_class='ModlandFile',
            parameter='/pub/modules/Screamtracker 3/Purple Motion/satellite one.s3m',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'openmpt')
        self.assertEqual(url, 'https://modland.ziphoid.com/pub/modules/Screamtracker 3/Purple Motion/satellite one.s3m')

    def test_modland_nonstandard(self):
        link = self.cybrev.links.create(
            link_class='ModlandFile',
            parameter='/pub/modules/OctaMED MMD0/Laxical/smoked.mmd0',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'openmpt')
        self.assertEqual(url, 'https://modland.ziphoid.com/pub/modules/OctaMED MMD0/Laxical/smoked.mmd0')

    def test_modland_psid(self):
        link = self.cybrev.links.create(
            link_class='ModlandFile',
            parameter='/pub/modules/PlaySID/Vincenzo/habvero.psid',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'sid')
        self.assertEqual(url, 'https://modland.ziphoid.com/pub/modules/PlaySID/Vincenzo/habvero.psid')

    def test_modland_sid(self):
        link = self.cybrev.links.create(
            link_class='ModlandFile',
            parameter='/pub/modules/PlaySID/Vincenzo/habvero.sid',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'sid')
        self.assertEqual(url, 'https://modland.ziphoid.com/pub/modules/PlaySID/Vincenzo/habvero.sid')

    def test_modland_sidmon(self):
        link = self.cybrev.links.create(
            link_class='ModlandFile',
            parameter='/pub/modules/SidMon%201/Romeo%20Knight/dinkelator.sid',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, None)
        self.assertEqual(url, None)

    def test_zxdemo(self):
        link = self.cybrev.links.create(
            link_class='BaseUrl',
            parameter='https://files.zxdemo.org/files/music/trk/B/Bzyk/AxelF.stc',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'stc')
        self.assertEqual(url, 'https://files.zxdemo.org/files/music/trk/B/Bzyk/AxelF.stc')

    def test_absencehq_pyg(self):
        link = self.cybrev.links.create(
            link_class='BaseUrl',
            parameter='https://absencehq.de/atari/pyg/Mad_Max/Games/Enchanted_Land_for_Cowbell_Player.pyg',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'pyg')
        self.assertEqual(url, 'https://absencehq.de/atari/pyg/Mad_Max/Games/Enchanted_Land_for_Cowbell_Player.pyg')

    def test_media_demozoo(self):
        link = self.cybrev.links.create(
            link_class='BaseUrl',
            parameter='https://media.demozoo.org/music/21/3d/zap.sid',
            is_download_link=True
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'sid')
        self.assertEqual(url, 'https://media.demozoo.org/music/21/3d/zap.sid')

    def test_modarchive(self):
        link = self.cybrev.links.create(
            link_class='ModarchiveModule',
            parameter='123',
            is_download_link=False
        )
        filetype, url = identify_link_as_track(link)
        self.assertEqual(filetype, 'openmpt')
        self.assertEqual(url, 'https://modarchive.org/jsplayer.php?moduleid=123')
