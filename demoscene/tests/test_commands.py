from __future__ import absolute_import, unicode_literals

from io import BytesIO

from django.core.files import File
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.test.utils import captured_stdout

from demoscene.models import Nick, NickVariant, Releaser
from demoscene.tests.utils import MediaTestMixin
from parties.models import Party, ResultsFile
from productions.models import Production, ProductionType


class TestBumpExternalLinks(TransactionTestCase):
    fixtures = ['tests/gasman.json']

    def test_run(self):
        mooncheese = Production.objects.get(title='Mooncheese')
        mooncheese.links.create(link_class='BaseUrl', parameter='https://www.pouet.net/prod.php?which=13121', is_download_link=False)
        mooncheese.links.create(link_class='SceneOrgFile', parameter='/mirrors/amigascne/Groups/A/Abandon/Abandon-NewDemosIntro', is_download_link=True)
        mooncheese.links.create(link_class='AmigascneFile', parameter='/Groups/A/Abandon/Abandon-NewDemosIntro', is_download_link=True)

        with captured_stdout():
            call_command('bump_external_links')

        self.assertTrue(
            mooncheese.links.filter(link_class='PouetProduction', parameter='13121').exists()
        )
        self.assertFalse(
            mooncheese.links.filter(link_class='SceneOrgFile').exists()
        )
        self.assertEqual(
            mooncheese.links.filter(link_class='AmigascneFile').count(), 1
        )


class TestSanity(MediaTestMixin, TestCase):
    fixtures = ['tests/gasman.json']

    def test_run(self):
        Releaser.objects.create(name='Okkie', is_group=False)
        Nick.objects.filter(name='Okkie').delete()
        NickVariant.objects.filter(name='Gasman').delete()
        Nick.objects.filter(name='Gasman').update(abbreviation='G')

        invitation_compo = Party.objects.get(name='Forever 2e3').competitions.create(
            name='Invitation compo'
        )
        mooncheese = Production.objects.get(title='Mooncheese')
        invitation_compo.placings.create(
            production=mooncheese,
            ranking=1, position=1
        )

        invitation_not_compo = Party.objects.get(name='Forever 2e3').competitions.create(
            name='Invitation not-compo'
        )
        invitation_not_compo.placings.create(
            production=Production.objects.get(title='Pondlife'),
            position=1
        )

        party = Party.objects.get(name="Forever 2e3")
        ResultsFile.objects.create(
            party=party,
            file=File(
                name="forever2e3.txt",
                file=BytesIO(b"You get a c\xe5r! You get a c\xe5r! Everybody gets a c\xe5r!")
            ),
            encoding='utf-8',
            filename="forever2e3.txt", filesize=100, sha1="1234123412341234"
        )
        results2 = ResultsFile.objects.create(
            party=party,
            file=File(
                name="forever2e3a.txt",
                file=BytesIO(b"hello")
            ),
            encoding='utf-8',
            filename="forever2e3.txt", filesize=100, sha1="1234123412341234"
        )
        results2.file.delete(save=False)

        madrielle = Production.objects.get(title='Madrielle')
        cybrev = Production.objects.get(title="Cybernoid's Revenge")
        danceallnight = Production.objects.create(title="Dance All Night", supertype="music")
        coverstory = Production.objects.create(title="Cover Story", supertype="music")
        madrielle.soundtrack_links.create(soundtrack=cybrev, position=1)
        madrielle.soundtrack_links.create(soundtrack=cybrev, position=2)
        madrielle.soundtrack_links.create(soundtrack=danceallnight, position=3)

        mooncheese.pack_members.create(member=coverstory, position=1)

        pondlife = Production.objects.get(title="Pondlife")
        pondlife.types.add(ProductionType.objects.get(name='Pack'))
        pondlife.pack_members.create(member=madrielle, position=1)
        pondlife.pack_members.create(member=madrielle, position=2)
        pondlife.pack_members.create(member=mooncheese, position=3)

        subxtc = Production.objects.create(title="Subliminal Extacy #1")
        subxtc.types.add(ProductionType.objects.get(name='Diskmag'))
        subxtc.pack_members.create(member=mooncheese, position=1)

        with captured_stdout():
            call_command('sanity')

        self.assertEqual(Nick.objects.filter(name='Okkie').count(), 1)
        self.assertEqual(NickVariant.objects.filter(name='Gasman').count(), 1)
        self.assertEqual(Nick.objects.get(name='Gasman').abbreviation, '')

        self.assertTrue(
            Party.objects.get(name='Forever 2e3').competitions.filter(name='Invitation compo').exists()
        )
        self.assertFalse(
            Party.objects.get(name='Forever 2e3').competitions.filter(name='Invitation not-compo').exists()
        )
        self.assertTrue(
            Party.objects.get(name='Forever 2e3').invitations.filter(title='Mooncheese').exists()
        )
        self.assertTrue(
            Party.objects.get(name='Forever 2e3').invitations.filter(title='Pondlife').exists()
        )

        self.assertEqual(
            Production.objects.get(title='Madrielle').soundtrack_links.filter(soundtrack=cybrev).count(), 1
        )
        self.assertEqual(
            Production.objects.get(title='Madrielle').soundtrack_links.get(soundtrack=danceallnight).position, 2
        )
        self.assertTrue(
            Production.objects.get(title='Mooncheese').soundtrack_links.filter(soundtrack=coverstory).exists()
        )
        self.assertFalse(
            Production.objects.get(title='Mooncheese').pack_members.filter(member=coverstory).exists()
        )
        self.assertEqual(
            Production.objects.get(title='Pondlife').pack_members.filter(member=madrielle).count(), 1
        )
        self.assertEqual(
            Production.objects.get(title='Pondlife').pack_members.get(member=mooncheese).position, 2
        )
        self.assertTrue(
            Production.objects.get(title='Subliminal Extacy #1').types.filter(name='Pack').exists()
        )
