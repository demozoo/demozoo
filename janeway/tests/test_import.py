from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from demoscene.models import Releaser
from janeway.importing import import_author, import_release
from janeway.models import Author, Release
from productions.models import Production


class TestImport(TestCase):
    fixtures = ['tests/gasman.json', 'tests/janeway.json']

    def test_import_group_first(self):
        import_author(Author.objects.get(name="Spaceballs"))
        import_author(Author.objects.get(name="TMB Designs"))
        import_release(Release.objects.get(title="State Of The Art"))

        self.assertTrue(Releaser.objects.filter(name="Spaceballs").exists())
        self.assertTrue(Releaser.objects.filter(name="TMB Designs").exists())
        self.assertTrue(
            Releaser.objects.get(name="TMB Designs").nicks.filter(name="TMB").exists()
        )
        self.assertTrue(
            Releaser.objects.get(name="Spaceballs").member_memberships.filter(
                member__name="TMB Designs"
            ).exists()
        )
        self.assertTrue(Production.objects.filter(title="State Of The Art").exists())
        self.assertTrue(
            Production.objects.get(title="State Of The Art").credits.filter(
                nick__name="TMB Designs"
            ).exists()
        )

    def test_import_member_first(self):
        import_author(Author.objects.get(name="TMB Designs"))
        import_author(Author.objects.get(name="Spaceballs"))
        import_release(Release.objects.get(title="State Of The Art"))

        self.assertTrue(Releaser.objects.filter(name="Spaceballs").exists())
        self.assertTrue(Releaser.objects.filter(name="TMB Designs").exists())
        self.assertTrue(
            Releaser.objects.get(name="TMB Designs").nicks.filter(name="TMB").exists()
        )
        self.assertTrue(
            Releaser.objects.get(name="Spaceballs").member_memberships.filter(
                member__name="TMB Designs"
            ).exists()
        )
        self.assertTrue(Production.objects.filter(title="State Of The Art").exists())
        self.assertTrue(
            Production.objects.get(title="State Of The Art").credits.filter(
                nick__name="TMB Designs"
            ).exists()
        )

    def test_case_insensitive_nick_match(self):
        tmb_janeway = Author.objects.get(name="TMB Designs")
        tmb_demozoo = Releaser.objects.create(name="TMB", is_group=False)
        tmb_designs_nick = tmb_demozoo.nicks.create(name="tmb designs")
        tmb_demozoo.external_links.create(link_class='KestraBitworldAuthor', parameter=tmb_janeway.janeway_id)

        import_author(Author.objects.get(name="Spaceballs"))
        import_release(Release.objects.get(title="State Of The Art"))
        self.assertTrue(
            Production.objects.get(title="State Of The Art").credits.filter(
                nick=tmb_designs_nick
            ).exists()
        )

    def test_releaser_without_nick_match(self):
        tmb_janeway = Author.objects.get(name="TMB Designs")
        tmb_demozoo = Releaser.objects.create(name="TMB", is_group=False)
        tmb_designs_nick = tmb_demozoo.nicks.create(name="not tmb designs")
        tmb_demozoo.external_links.create(link_class='KestraBitworldAuthor', parameter=tmb_janeway.janeway_id)

        import_author(Author.objects.get(name="Spaceballs"))
        import_release(Release.objects.get(title="State Of The Art"))
        self.assertTrue(
            Production.objects.get(title="State Of The Art").credits.filter(
                nick=tmb_demozoo.primary_nick
            ).exists()
        )
