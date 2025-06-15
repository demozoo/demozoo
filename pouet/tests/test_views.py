from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Releaser
from productions.models import Production


class TestGroupsView(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_get(self):
        response = self.client.get("/pouet/groups/")
        self.assertEqual(response.status_code, 200)

    def test_get_full(self):
        response = self.client.get("/pouet/groups/?mode=full")
        self.assertEqual(response.status_code, 200)

    def test_get_pouet_unmatched(self):
        response = self.client.get("/pouet/groups/?mode=pouet_unmatched")
        self.assertEqual(response.status_code, 200)

    def test_get_nogroup_productions(self):
        response = self.client.get("/pouet/nogroup-prods/")
        self.assertEqual(response.status_code, 200)


class TestMatchGroup(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_get(self):
        hprg = Releaser.objects.get(name="Hooy-Program")
        response = self.client.get("/pouet/groups/%d/" % hprg.id)
        self.assertEqual(response.status_code, 200)


class TestProductionLink(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_post(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.post(
            "/pouet/production-link/",
            {
                "demozoo_id": pondlife.id,
                "pouet_id": "2611",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(pondlife.links.filter(link_class="PouetProduction", parameter="2611").exists())


class TestProductionUnink(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_post(self):
        pondlife = Production.objects.get(title="Pondlife")
        pondlife.links.create(link_class="PouetProduction", parameter="2611", is_download_link=False)
        response = self.client.post(
            "/pouet/production-unlink/",
            {
                "demozoo_id": pondlife.id,
                "pouet_id": "2611",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pondlife.links.filter(link_class="PouetProduction", parameter="2611").exists())
