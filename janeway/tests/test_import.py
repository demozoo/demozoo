from django.test import TestCase

from demoscene.models import Releaser
from janeway.importing import import_author, import_release
from janeway.models import Author, Release
from productions.models import Production


class TestImport(TestCase):
    fixtures = ["tests/gasman.json", "tests/janeway.json"]

    def test_import_group_first(self):
        import_author(Author.objects.get(name="Spaceballs"))
        import_author(Author.objects.get(name="TMB Designs"))
        import_release(Release.objects.get(title="State Of The Art"))

        self.assertTrue(Releaser.objects.filter(name="Spaceballs").exists())
        self.assertTrue(Releaser.objects.filter(name="TMB Designs").exists())
        self.assertTrue(Releaser.objects.get(name="TMB Designs").nicks.filter(name="TMB").exists())
        self.assertTrue(
            Releaser.objects.get(name="Spaceballs").member_memberships.filter(member__name="TMB Designs").exists()
        )
        sota = Production.objects.get(title="State Of The Art")
        self.assertTrue(sota.credits.filter(nick__name="TMB Designs").exists())
        self.assertTrue(sota.platforms.filter(name="Amiga OCS/ECS").exists())
        self.assertTrue(
            sota.links.filter(
                link_class="AmigascneFile",
                parameter="/Groups/S/Spaceballs/Spaceballs-StateOfTheArt.dms",
                source="janeway",
            ).exists()
        )

    def test_import_member_first(self):
        import_author(Author.objects.get(name="TMB Designs"))
        import_author(Author.objects.get(name="Spaceballs"))
        import_release(Release.objects.get(title="State Of The Art"))

        self.assertTrue(Releaser.objects.filter(name="Spaceballs").exists())
        self.assertTrue(Releaser.objects.filter(name="TMB Designs").exists())
        self.assertTrue(Releaser.objects.get(name="TMB Designs").nicks.filter(name="TMB").exists())
        self.assertTrue(
            Releaser.objects.get(name="Spaceballs").member_memberships.filter(member__name="TMB Designs").exists()
        )
        sota = Production.objects.get(title="State Of The Art")
        self.assertTrue(sota.credits.filter(nick__name="TMB Designs").exists())
        self.assertTrue(sota.platforms.filter(name="Amiga OCS/ECS").exists())

    def test_import_aga(self):
        import_release(Release.objects.get(title="Ocean Machine"))
        ocean_machine = Production.objects.get(title="Ocean Machine")
        self.assertTrue(ocean_machine.platforms.filter(name="Amiga AGA").exists())

    def test_import_ppc(self):
        import_release(Release.objects.get(title="Planet Potion"))
        planet_potion = Production.objects.get(title="Planet Potion")
        self.assertTrue(planet_potion.platforms.filter(name="Amiga PPC/RTG").exists())

    def test_case_insensitive_nick_match(self):
        tmb_janeway = Author.objects.get(name="TMB Designs")
        tmb_demozoo = Releaser.objects.create(name="TMB", is_group=False)
        tmb_designs_nick = tmb_demozoo.nicks.create(name="tmb designs")
        tmb_demozoo.external_links.create(link_class="KestraBitworldAuthor", parameter=tmb_janeway.janeway_id)

        import_author(Author.objects.get(name="Spaceballs"))
        import_release(Release.objects.get(title="State Of The Art"))
        self.assertTrue(Production.objects.get(title="State Of The Art").credits.filter(nick=tmb_designs_nick).exists())

    def test_releaser_without_nick_match(self):
        tmb_janeway = Author.objects.get(name="TMB Designs")
        tmb_demozoo = Releaser.objects.create(name="TMB", is_group=False)
        tmb_demozoo.nicks.create(name="not tmb designs")
        tmb_demozoo.external_links.create(link_class="KestraBitworldAuthor", parameter=tmb_janeway.janeway_id)

        import_author(Author.objects.get(name="Spaceballs"))
        import_release(Release.objects.get(title="State Of The Art"))
        self.assertTrue(
            Production.objects.get(title="State Of The Art").credits.filter(nick=tmb_demozoo.primary_nick).exists()
        )

    def test_import_packcontent_pack_first(self):
        import_release(Release.objects.get(title="Spaceballs Pack 1"))
        import_release(Release.objects.get(title="State Of The Art"))
        pack = Production.objects.get(title="Spaceballs Pack 1")
        self.assertTrue(pack.pack_members.filter(member__title="State Of The Art").exists())

    def test_import_packcontent_member_first(self):
        import_release(Release.objects.get(title="State Of The Art"))
        import_release(Release.objects.get(title="Spaceballs Pack 1"))
        pack = Production.objects.get(title="Spaceballs Pack 1")
        self.assertTrue(pack.pack_members.filter(member__title="State Of The Art").exists())

    def test_import_soundtracklink_soundtrack_first(self):
        import_release(Release.objects.get(title="mod.condom_corruption"))
        import_release(Release.objects.get(title="State Of The Art"))
        sota = Production.objects.get(title="State Of The Art")
        self.assertTrue(sota.soundtrack_links.filter(soundtrack__title="condom_corruption").exists())

    def test_import_soundtracklink_prod_first(self):
        import_release(Release.objects.get(title="State Of The Art"))
        import_release(Release.objects.get(title="mod.condom_corruption"))
        sota = Production.objects.get(title="State Of The Art")
        self.assertTrue(sota.soundtrack_links.filter(soundtrack__title="condom_corruption").exists())
