import json

from django.test import TestCase, override_settings

from bbs.models import BBS
from parties.models import Competition, CompetitionPlacing, Party, PartySeries
from productions.models import Production


class TestApiRoot(TestCase):
    def test_get_root(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("platforms", response_data)
        self.assertIn("productions", response_data)
        self.assertIn("releasers", response_data)
        self.assertIn("production_types", response_data)

    def test_get_browsable_api(self):
        response = self.client.get("/api/v1/?format=api")
        self.assertEqual(response.status_code, 200)


class TestPlatforms(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_platforms(self):
        response = self.client.get("/api/v1/platforms/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("ZX Spectrum", [result["name"] for result in response_data["results"]])


class TestProdTypes(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_prod_types(self):
        response = self.client.get("/api/v1/production_types/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("Demo", [result["name"] for result in response_data["results"]])


class TestProductions(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_productions(self):
        response = self.client.get("/api/v1/productions/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        pondlife = [result for result in response_data["results"] if result["title"] == "Pondlife"][0]
        self.assertIn("Hooy-Program", [nick["name"] for nick in pondlife["author_nicks"]])

    def test_filter_by_author(self):
        response = self.client.get("/api/v1/productions/?author=4")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        result_titles = [result["title"] for result in response_data["results"]]
        self.assertIn("Pondlife", result_titles)
        self.assertNotIn("Madrielle", result_titles)

    def test_fields_param(self):
        response = self.client.get("/api/v1/productions/?title=Madrielle&fields=id,title,competition_placings")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        result = response_data["results"][0]
        self.assertEqual(result["title"], "Madrielle")
        self.assertNotIn("demozoo_url", result)
        self.assertEqual(result["competition_placings"][0]["competition"]["name"], "ZX 1K Intro")

    def test_filter_by_competition_placing(self):
        pondlife = Production.objects.get(title="Pondlife")
        madrielle = Production.objects.get(title="Madrielle")
        compo = Competition.objects.get(name="ZX 1K Intro")
        madrielle_placing = madrielle.competition_placings.first()
        madrielle_placing.position = 2
        madrielle_placing.save()
        CompetitionPlacing.objects.create(
            competition=compo,
            production=pondlife,
            position=1,
            ranking="1",
            score="100",
        )

        response = self.client.get("/api/v1/productions/?competition_placing_min=1")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        result_titles = [result["title"] for result in response_data["results"]]
        self.assertIn("Pondlife", result_titles)
        self.assertNotIn("Madrielle", result_titles)

    @override_settings(BASE_URL="https://demozoo.org")
    def test_get_production(self):
        response = self.client.get("/api/v1/productions/4/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["title"], "Pondlife")
        self.assertEqual(response_data["demozoo_url"], "https://demozoo.org/productions/4/")
        self.assertIn("Hooy-Program", [nick["name"] for nick in response_data["author_nicks"]])


class TestReleasers(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_releasers(self):
        response = self.client.get("/api/v1/releasers/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("Gasman", [result["name"] for result in response_data["results"]])

    def test_get_releaser(self):
        response = self.client.get("/api/v1/releasers/2/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["name"], "Raww Arse")
        self.assertIn("Papaya Dezign", [subgroupage["subgroup"]["name"] for subgroupage in response_data["subgroups"]])
        self.assertIn("Gasman", [membership["member"]["name"] for membership in response_data["members"]])

    def test_get_releaser_prods(self):
        response = self.client.get("/api/v1/releasers/2/productions/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("Pondlife", [result["title"] for result in response_data])

    def test_get_releaser_member_prods(self):
        response = self.client.get("/api/v1/releasers/2/member_productions/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("Madrielle", [result["title"] for result in response_data])


class TestPartySeries(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_serieses(self):
        response = self.client.get("/api/v1/party_series/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("Forever", [result["name"] for result in response_data["results"]])

    def test_get_series(self):
        forever = PartySeries.objects.get(name="Forever")
        response = self.client.get("/api/v1/party_series/%d/" % forever.id)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["name"], "Forever")


class TestParties(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_parties(self):
        response = self.client.get("/api/v1/parties/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("Forever 2e3", [result["name"] for result in response_data["results"]])

    def test_get_party(self):
        forever = Party.objects.get(name="Forever 2e3")
        response = self.client.get("/api/v1/parties/%d/" % forever.id)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["name"], "Forever 2e3")


class TestBBSes(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get_bbses(self):
        response = self.client.get("/api/v1/bbses/")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertIn("StarPort", [result["name"] for result in response_data["results"]])

    def test_get_bbs(self):
        starport = BBS.objects.get(name="StarPort")
        response = self.client.get("/api/v1/bbses/%d/" % starport.id)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(response_data["name"], "StarPort")
