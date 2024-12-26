from io import BytesIO

from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from bbs.models import BBS, Affiliation, BBSExternalLink, Operator
from demoscene.models import Edit, Releaser
from demoscene.tests.utils import MediaTestMixin
from productions.models import Production


class TestIndex(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        response = self.client.get("/bbs/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StarPort")

    def test_get_ordered_by_date_added(self):
        response = self.client.get("/bbs/?order=added&dir=desc")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StarPort")


class TestTagIndex(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        bbs = BBS.objects.get(name="StarPort")
        bbs.tags.add("future-crew")
        response = self.client.get("/bbs/tagged/future-crew/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StarPort")

    def test_get_nonexistent(self):
        response = self.client.get("/bbs/tagged/this-does-not-exist/")
        self.assertEqual(response.status_code, 200)


class TestShow(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        bbs = BBS.objects.get(name="StarPort")
        response = self.client.get("/bbs/%d/" % bbs.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "StarPort")
        self.assertContains(response, "<b>Star Port episode IV: A New Hope</b>")


class TestCreate(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_get(self):
        response = self.client.get("/bbs/new/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/new/",
            {
                "name": "Eclipse",
                "location": "",
                "names-TOTAL_FORMS": "0",
                "names-INITIAL_FORMS": "0",
                "names-MIN_NUM_FORMS": "0",
                "names-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % BBS.objects.get(name="Eclipse").id)

    def test_create_with_alternative_name(self):
        response = self.client.post(
            "/bbs/new/",
            {
                "name": "Eclipse",
                "location": "",
                "names-TOTAL_FORMS": "1",
                "names-INITIAL_FORMS": "0",
                "names-MIN_NUM_FORMS": "0",
                "names-MAX_NUM_FORMS": "1000",
                "names-0-name": "Total Eclipse",
            },
        )
        bbs = BBS.objects.get(name="Eclipse")
        self.assertRedirects(response, "/bbs/%d/" % bbs.id)
        self.assertEqual(bbs.names.count(), 2)
        self.assertTrue(bbs.names.filter(name="Eclipse").exists())
        self.assertTrue(bbs.names.filter(name="Total Eclipse").exists())


class TestEdit(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.alt_name = self.bbs.alternative_names.first()

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get("/bbs/%d/edit/" % self.bbs.id)
        self.assertRedirects(response, "/account/login/?next=/bbs/%d/" % self.bbs.id)

    def test_get(self):
        response = self.client.get("/bbs/%d/edit/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/edit/" % self.bbs.id,
            {
                "name": "StarWhisky",
                "location": "Oxford",
                "names-TOTAL_FORMS": "1",
                "names-INITIAL_FORMS": "1",
                "names-MIN_NUM_FORMS": "0",
                "names-MAX_NUM_FORMS": "1000",
                "names-0-name": "Star Whisky episode IV: A New Hope",
                "names-0-id": self.alt_name.id,
                "names-0-bbs": self.bbs.id,
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)
        self.bbs.refresh_from_db()
        self.assertEqual(self.bbs.name, "StarWhisky")
        self.assertEqual(self.bbs.names.count(), 2)
        self.assertTrue(self.bbs.names.filter(name="StarWhisky").exists())
        self.assertTrue(self.bbs.names.filter(name="Star Whisky episode IV: A New Hope").exists())
        edit = Edit.for_model(self.bbs, True).first()
        self.assertEqual(
            "Set name to 'StarWhisky', location to Oxford, alternative names to " "Star Whisky episode IV: A New Hope",
            edit.description,
        )

    def test_post_edit_alternate_names_only(self):
        response = self.client.post(
            "/bbs/%d/edit/" % self.bbs.id,
            {
                "name": "StarPort",
                "location": "Helsinki, Finland",
                "names-TOTAL_FORMS": "1",
                "names-INITIAL_FORMS": "1",
                "names-MIN_NUM_FORMS": "0",
                "names-MAX_NUM_FORMS": "1000",
                "names-0-name": "Star Whisky episode V",
                "names-0-id": self.alt_name.id,
                "names-0-bbs": self.bbs.id,
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)
        self.bbs.refresh_from_db()
        self.assertEqual(self.bbs.name, "StarPort")
        self.assertEqual(self.bbs.names.count(), 2)
        self.assertTrue(self.bbs.names.filter(name="StarPort").exists())
        self.assertTrue(self.bbs.names.filter(name="Star Whisky episode V").exists())
        edit = Edit.for_model(self.bbs, True).first()
        self.assertEqual("Set alternative names to Star Whisky episode V", edit.description)


class TestEditNotes(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")

    def test_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/bbs/%d/edit_notes/" % self.bbs.id)
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)

    def test_get(self):
        response = self.client.get("/bbs/%d/edit_notes/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/edit_notes/" % self.bbs.id,
            {
                "notes": "purple motion ad lib music etc",
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)


class TestDelete(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")

    def test_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/bbs/%d/delete/" % self.bbs.id)
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)

    def test_get(self):
        response = self.client.get("/bbs/%d/delete/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post("/bbs/%d/delete/" % self.bbs.id, {"yes": "yes"})
        self.assertRedirects(response, "/bbs/")
        self.assertFalse(BBS.objects.filter(name="StarPort").exists())

    def test_cancel(self):
        response = self.client.post("/bbs/%d/delete/" % self.bbs.id, {"no": "no"})
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)
        self.assertTrue(BBS.objects.filter(name="StarPort").exists())


class TestEditBBStros(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.pondlife = Production.objects.get(title="Pondlife")

    def test_get(self):
        response = self.client.get("/bbs/%d/edit_bbstros/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/edit_bbstros/" % self.bbs.id,
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": self.pondlife.id,
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "",
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)
        self.assertEqual(self.bbs.bbstros.count(), 1)

        edit = Edit.for_model(self.bbs, True).first()
        self.assertEqual("Set promoted in to Pondlife", edit.description)

        # no change => no edit log entry added
        edit_count = Edit.for_model(self.bbs, True).count()
        response = self.client.post(
            "/bbs/%d/edit_bbstros/" % self.bbs.id,
            {
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 1,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
                "form-0-production_id": self.pondlife.id,
                "form-0-production_title": "Pondlife",
                "form-0-production_byline_search": "",
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)
        self.assertEqual(edit_count, Edit.for_model(self.bbs, True).count())


class TestShowHistory(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        bbs = BBS.objects.get(name="StarPort")
        response = self.client.get("/bbs/%d/history/" % bbs.id)
        self.assertEqual(response.status_code, 200)


class TestAddOperator(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.gasman = Releaser.objects.get(name="Gasman")

    def test_get(self):
        response = self.client.get("/bbs/%d/add_operator/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/add_operator/" % self.bbs.id,
            {
                "releaser_nick_search": "gasman",
                "releaser_nick_match_id": self.gasman.primary_nick.id,
                "releaser_nick_match_name": "gasman",
                "role": "co-sysop",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=staff" % self.bbs.id)
        self.assertEqual(1, Operator.objects.filter(releaser=self.gasman, bbs=self.bbs).count())


class TestEditOperator(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.abyss = Releaser.objects.get(name="Abyss")
        self.yerzmyey = Releaser.objects.get(name="Yerzmyey")
        self.operator = Operator.objects.get(bbs=self.bbs, releaser=self.abyss)

    def test_get(self):
        response = self.client.get("/bbs/%d/edit_operator/%d/" % (self.bbs.id, self.operator.id))
        self.assertEqual(response.status_code, 200)

    def test_post_set_current(self):
        self.operator.is_current = False
        self.operator.save()

        response = self.client.post(
            "/bbs/%d/edit_operator/%d/" % (self.bbs.id, self.operator.id),
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "co-sysop",
                "is_current": "is_current",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=staff" % self.bbs.id)
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.role, "co-sysop")
        self.assertEqual(self.operator.releaser, self.yerzmyey)
        self.assertTrue(self.operator.is_current)
        edit = Edit.for_model(self.yerzmyey, True).first()
        self.assertIn("set as current staff", edit.description)

    def test_post_set_not_current(self):
        response = self.client.post(
            "/bbs/%d/edit_operator/%d/" % (self.bbs.id, self.operator.id),
            {
                "releaser_nick_search": "yerzmyey",
                "releaser_nick_match_id": self.yerzmyey.primary_nick.id,
                "releaser_nick_match_name": "yerzmyey",
                "role": "co-sysop",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=staff" % self.bbs.id)
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.role, "co-sysop")
        self.assertEqual(self.operator.releaser, self.yerzmyey)
        self.assertFalse(self.operator.is_current)
        edit = Edit.for_model(self.yerzmyey, True).first()
        self.assertIn("set as ex-staff", edit.description)


class TestRemoveOperator(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.abyss = Releaser.objects.get(name="Abyss")
        self.operator = Operator.objects.get(bbs=self.bbs, releaser=self.abyss)

    def test_get(self):
        response = self.client.get("/bbs/%d/remove_operator/%d/" % (self.bbs.id, self.operator.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/remove_operator/%d/" % (self.bbs.id, self.operator.id),
            {
                "yes": "yes",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=staff" % self.bbs.id)
        self.assertEqual(0, Operator.objects.filter(releaser=self.abyss, bbs=self.bbs).count())


class TestAddAffiliation(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.hprg = Releaser.objects.get(name="Hooy-Program")

    def test_get(self):
        response = self.client.get("/bbs/%d/add_affiliation/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/add_affiliation/" % self.bbs.id,
            {
                "group_nick_search": "hooy-program",
                "group_nick_match_id": self.hprg.primary_nick.id,
                "group_nick_match_name": "hooy-program",
                "role": "020-hq",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=affiliations" % self.bbs.id)
        self.assertEqual(1, Affiliation.objects.filter(group=self.hprg, bbs=self.bbs).count())

    def test_post_blank_role(self):
        response = self.client.post(
            "/bbs/%d/add_affiliation/" % self.bbs.id,
            {
                "group_nick_search": "hooy-program",
                "group_nick_match_id": self.hprg.primary_nick.id,
                "group_nick_match_name": "hooy-program",
                "role": "",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=affiliations" % self.bbs.id)
        self.assertEqual(1, Affiliation.objects.filter(group=self.hprg, bbs=self.bbs).count())


class TestEditAffiliation(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.fc = Releaser.objects.get(name="Future Crew")
        self.hprg = Releaser.objects.get(name="Hooy-Program")
        self.affiliation = Affiliation.objects.get(bbs=self.bbs, group=self.fc)

    def test_get(self):
        response = self.client.get("/bbs/%d/edit_affiliation/%d/" % (self.bbs.id, self.affiliation.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/edit_affiliation/%d/" % (self.bbs.id, self.affiliation.id),
            {
                "group_nick_search": "hooy-program",
                "group_nick_match_id": self.hprg.primary_nick.id,
                "group_nick_match_name": "hooy-program",
                "role": "020-hq",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=affiliations" % self.bbs.id)
        self.affiliation.refresh_from_db()
        self.assertEqual(self.affiliation.role, "020-hq")
        self.assertEqual(self.affiliation.group, self.hprg)


class TestRemoveAffiliation(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")
        self.fc = Releaser.objects.get(name="Future Crew")
        self.affiliation = Affiliation.objects.get(bbs=self.bbs, group=self.fc)

    def test_get(self):
        response = self.client.get("/bbs/%d/remove_affiliation/%d/" % (self.bbs.id, self.affiliation.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/remove_affiliation/%d/" % (self.bbs.id, self.affiliation.id),
            {
                "yes": "yes",
            },
        )
        self.assertRedirects(response, "/bbs/%d/?editing=affiliations" % self.bbs.id)
        self.assertEqual(0, Affiliation.objects.filter(group=self.fc, bbs=self.bbs).count())


class TestEditTextAds(MediaTestMixin, TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.starport = BBS.objects.get(name="StarPort")

        self.info1 = self.starport.text_ads.create(
            file=File(name="starport1.txt", file=BytesIO(b"First text ad for StarPort")),
            filename="starport1.txt",
            filesize=100,
            sha1="1234123412341234",
        )
        self.info2 = self.starport.text_ads.create(
            file=File(name="starport2.txt", file=BytesIO(b"Second text ad for StarPort")),
            filename="starport2.txt",
            filesize=100,
            sha1="1234123412341235",
        )

    def test_get_as_normal_user(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/bbs/%d/edit_text_ads/" % self.starport.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adding text ad for StarPort")

    def test_get_as_superuser(self):
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.get("/bbs/%d/edit_text_ads/" % self.starport.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editing text ads for StarPort")

    def test_add_one(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            "/bbs/%d/edit_text_ads/" % self.starport.id,
            {"text_ad": SimpleUploadedFile("starport3.txt", b"Third text ad", content_type="text/plain")},
        )
        self.assertRedirects(response, "/bbs/%d/" % self.starport.id)
        self.assertEqual(3, self.starport.text_ads.count())

    def test_add_multiple(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            "/bbs/%d/edit_text_ads/" % self.starport.id,
            {
                "text_ad": [
                    SimpleUploadedFile("starport3.txt", b"Third text ad", content_type="text/plain"),
                    SimpleUploadedFile("starport4.txt", b"Fourth text ad", content_type="text/plain"),
                ]
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.starport.id)
        self.assertEqual(4, self.starport.text_ads.count())

    def test_delete_one(self):
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.post(
            "/bbs/%d/edit_text_ads/" % self.starport.id,
            {
                "text_ads-TOTAL_FORMS": 2,
                "text_ads-INITIAL_FORMS": 2,
                "text_ads-MIN_NUM_FORMS": 0,
                "text_ads-MAX_NUM_FORMS": 1000,
                "text_ads-0-DELETE": "text_ads-0-DELETE",
                "text_ads-0-id": self.info1.id,
                "text_ads-0-bbs": self.starport.id,
                "text_ads-1-id": self.info2.id,
                "text_ads-1-bbs": self.starport.id,
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.starport.id)
        self.assertEqual(1, self.starport.text_ads.count())

    def test_delete_multiple(self):
        self.client.login(username="testsuperuser", password="12345")
        response = self.client.post(
            "/bbs/%d/edit_text_ads/" % self.starport.id,
            {
                "text_ads-TOTAL_FORMS": 2,
                "text_ads-INITIAL_FORMS": 2,
                "text_ads-MIN_NUM_FORMS": 0,
                "text_ads-MAX_NUM_FORMS": 1000,
                "text_ads-0-DELETE": "text_ads-0-DELETE",
                "text_ads-0-id": self.info1.id,
                "text_ads-0-bbs": self.starport.id,
                "text_ads-1-DELETE": "text_ads-1-DELETE",
                "text_ads-1-id": self.info2.id,
                "text_ads-1-bbs": self.starport.id,
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.starport.id)
        self.assertEqual(0, self.starport.text_ads.count())


class TestTextAd(MediaTestMixin, TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.starport = BBS.objects.get(name="StarPort")
        self.info = self.starport.text_ads.create(
            file=File(name="starport1.txt", file=BytesIO(b"First text ad for StarPort")),
            filename="starport1.txt",
            filesize=100,
            sha1="1234123412341234",
        )
        self.info2 = self.starport.text_ads.create(
            file=File(name="starport2.ans", file=BytesIO(b"Second \x1b[32mtext ad\x1b[37m for \xcdStarPort\xcd")),
            filename="starport2.ans",
            filesize=100,
            sha1="1234123412341234",
        )

    def test_get_without_login(self):
        url = "/bbs/%d/text_ad/%d/" % (self.starport.id, self.info.id)
        response = self.client.get(url)
        self.assertRedirects(response, "/account/login/?next=%s" % url)

    def test_get_with_login(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/bbs/%d/text_ad/%d/" % (self.starport.id, self.info.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First text ad for StarPort")
        self.assertContains(response, 'class="text-file "')

    def test_get_ansi(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get("/bbs/%d/text_ad/%d/" % (self.starport.id, self.info2.id))
        self.assertEqual(response.status_code, 200)
        # should be recognised as ansi
        self.assertContains(response, 'class="text-file ansi"')
        # should decode as cp437 as the default option
        self.assertContains(response, "\u2550StarPort\u2550")


class TestEditTags(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.starport = BBS.objects.get(name="StarPort")

    def test_post(self):
        response = self.client.post("/bbs/%d/edit_tags/" % self.starport.id, {"tags": "future-crew,finland"})
        self.assertRedirects(response, "/bbs/%d/" % self.starport.id)
        self.assertEqual(self.starport.tags.count(), 2)


class TestAddTag(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.starport = BBS.objects.get(name="StarPort")

    def test_post(self):
        response = self.client.post("/bbs/%d/add_tag/" % self.starport.id, {"tag_name": "future-crew"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.starport.tags.count(), 1)


class TestRemoveTag(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.starport = BBS.objects.get(name="StarPort")
        self.starport.tags.add("future-crew")

    def test_post(self):
        response = self.client.post("/bbs/%d/remove_tag/" % self.starport.id, {"tag_name": "future-crew"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.starport.tags.count(), 0)


class TestEditExternalLinks(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")
        self.bbs = BBS.objects.get(name="StarPort")

    def test_get(self):
        response = self.client.get("/bbs/%d/edit_external_links/" % self.bbs.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            "/bbs/%d/edit_external_links/" % self.bbs.id,
            {
                "external_links-TOTAL_FORMS": 1,
                "external_links-INITIAL_FORMS": 0,
                "external_links-MIN_NUM_FORMS": 0,
                "external_links-MAX_NUM_FORMS": 1000,
                "external_links-0-url": "https://csdb.dk/bbs/?id=2184",
                "external_links-0-bbs": self.bbs.id,
            },
        )
        self.assertRedirects(response, "/bbs/%d/" % self.bbs.id)
        self.assertEqual(BBSExternalLink.objects.filter(bbs=self.bbs, link_class="CsdbBBS").count(), 1)
