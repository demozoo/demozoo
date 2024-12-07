import json

from django.test import TestCase

from demoscene.models import Nick, Releaser


class TestMatchNick(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        self.gasman_nick = Nick.objects.get(name="Gasman")
        self.hprg = Releaser.objects.get(name="Hooy-Program")
        self.hprg_nick = Nick.objects.get(name="Hooy-Program")

    def test_autocomplete_scener_name(self):
        response = self.client.get("/nicks/match/?q=gas&autocomplete=true&sceners_only=true")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result["initial_query"], "gas")
        self.assertEqual(result["query"], "gasman")
        self.assertEqual(result["match"]["selection"], {"id": self.gasman_nick.id, "name": "gasman"})
        self.assertEqual(len(result["match"]["choices"]), 2)
        self.assertEqual(result["match"]["choices"][0]["id"], self.gasman_nick.id)
        self.assertEqual(result["match"]["choices"][1]["id"], "newscener")

    def test_autocomplete_scener_name_with_group(self):
        response = self.client.get(
            "/nicks/match/?q=gas&autocomplete=true&sceners_only=true&group_ids=%d" % self.hprg.id
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result["initial_query"], "gas")
        self.assertEqual(result["query"], "gasman")
        self.assertEqual(result["match"]["selection"], {"id": self.gasman_nick.id, "name": "gasman"})
        self.assertEqual(len(result["match"]["choices"]), 2)
        self.assertEqual(result["match"]["choices"][0]["id"], self.gasman_nick.id)
        self.assertEqual(result["match"]["choices"][1]["id"], "newscener")

    def test_autocomplete_group_name(self):
        response = self.client.get("/nicks/match/?q=hooy&autocomplete=true&groups_only=true")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result["initial_query"], "hooy")
        self.assertEqual(result["query"], "hooy-Program")
        self.assertEqual(result["match"]["selection"], {"id": self.hprg_nick.id, "name": "hooy-Program"})
        self.assertEqual(len(result["match"]["choices"]), 2)
        self.assertEqual(result["match"]["choices"][0]["id"], self.hprg_nick.id)
        self.assertEqual(result["match"]["choices"][1]["id"], "newgroup")

    def test_look_up_scener_name(self):
        response = self.client.get("/nicks/match/?q=gasman&autocomplete=false&sceners_only=true")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result["initial_query"], "gasman")
        self.assertEqual(result["query"], "gasman")
        self.assertEqual(result["match"]["selection"], {"id": self.gasman_nick.id, "name": "gasman"})
        self.assertEqual(len(result["match"]["choices"]), 2)
        self.assertEqual(result["match"]["choices"][0]["id"], self.gasman_nick.id)
        self.assertEqual(result["match"]["choices"][1]["id"], "newscener")

    def test_autocomplete_full_name(self):
        response = self.client.get("/nicks/match/?q=gasman&autocomplete=true")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result["initial_query"], "gasman")
        self.assertEqual(result["query"], "gasman")
        self.assertEqual(result["match"]["selection"], {"id": self.gasman_nick.id, "name": "gasman"})
        self.assertEqual(len(result["match"]["choices"]), 3)
        self.assertEqual(result["match"]["choices"][0]["id"], self.gasman_nick.id)
        self.assertEqual(result["match"]["choices"][1]["id"], "newscener")
        self.assertEqual(result["match"]["choices"][2]["id"], "newgroup")

    def test_autocomplete_no_results(self):
        response = self.client.get("/nicks/match/?q=adsfasdfasdfsf&autocomplete=true")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result["initial_query"], "adsfasdfasdfsf")
        self.assertEqual(result["query"], "adsfasdfasdfsf")
        self.assertEqual(result["match"]["selection"], {"id": None, "name": "adsfasdfasdfsf"})
        self.assertEqual(len(result["match"]["choices"]), 2)
        self.assertEqual(result["match"]["choices"][0]["id"], "newscener")
        self.assertEqual(result["match"]["choices"][1]["id"], "newgroup")


class TestMatchByline(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        response = self.client.get("/nicks/byline_match/?q=gasman%2fhoo&autocomplete=true")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/nicks/byline_match/?q=gasman&autocomplete=true")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/nicks/byline_match/?q=gasman%2fhprg&autocomplete=false")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/nicks/byline_match/?q=zxcvzxcv&autocomplete=true")
        self.assertEqual(response.status_code, 200)
