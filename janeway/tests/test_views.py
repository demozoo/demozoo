from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Releaser, ReleaserExternalLink
from janeway.models import Author, Release
from productions.models import Production, ProductionLink


class TestAuthorsIndex(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")

    def test_get(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/janeway/authors/")
        self.assertEqual(response.status_code, 200)

    def test_get_full(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/janeway/authors/?full=1")
        self.assertEqual(response.status_code, 200)


class TestMatchAuthor(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.gasman = Releaser.objects.get(name="Gasman")

    def test_get(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/janeway/authors/%d/" % self.gasman.id)
        self.assertEqual(response.status_code, 200)


class TestProductionLink(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.pondlife = Production.objects.get(title="Pondlife")

    def test_post(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            "/janeway/production-link/",
            {
                "demozoo_id": self.pondlife.id,
                "janeway_id": 123,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ProductionLink.objects.filter(
                link_class="KestraBitworldRelease", parameter="123", production=self.pondlife
            ).exists()
        )


class TestProductionUnlink(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.pondlife = Production.objects.get(title="Pondlife")
        ProductionLink.objects.create(link_class="KestraBitworldRelease", parameter="123", production=self.pondlife)

    def test_post(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            "/janeway/production-unlink/",
            {
                "demozoo_id": self.pondlife.id,
                "janeway_id": 123,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            ProductionLink.objects.filter(
                link_class="KestraBitworldRelease", parameter="123", production=self.pondlife
            ).exists()
        )


class TestProductionImport(TestCase):
    fixtures = ["tests/janeway.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.sota = Release.objects.get(title="State Of The Art")
        self.patarty = Release.objects.get(title="MOD.patarty.gz")

    def test_non_superuser(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post("/janeway/production-import/", {"janeway_id": self.sota.janeway_id})
        self.assertRedirects(response, "/")
        self.assertFalse(Production.objects.filter(title="State Of The Art").exists())

    def test_post(self):
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.post("/janeway/production-import/", {"janeway_id": self.sota.janeway_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Production.objects.filter(title="State Of The Art").exists())

    def test_clean_music_title(self):
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.post("/janeway/production-import/", {"janeway_id": self.patarty.janeway_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Production.objects.filter(title="patarty").exists())


class TestAuthorProductionsImport(TestCase):
    fixtures = ["tests/janeway.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        janeway_spb = Author.objects.get(name="Spaceballs")
        self.demozoo_spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        ReleaserExternalLink.objects.create(
            link_class="KestraBitworldAuthor", parameter=janeway_spb.janeway_id, releaser=self.demozoo_spb
        )

    def test_non_superuser(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post("/janeway/import-all-author-productions/", {"releaser_id": self.demozoo_spb.id})
        self.assertRedirects(response, "/")
        self.assertFalse(Production.objects.filter(title="State Of The Art").exists())

    def test_post(self):
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.post("/janeway/import-all-author-productions/", {"releaser_id": self.demozoo_spb.id})
        self.assertRedirects(response, "/janeway/authors/%d/" % self.demozoo_spb.id)
        self.assertTrue(Production.objects.filter(title="State Of The Art").exists())
