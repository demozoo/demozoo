from django import forms
from django.test import TestCase

from demoscene.fields import MatchedNickField, NickField, NickLookup, NickSearch, NickSelection


class TestNickSelection(TestCase):
    def test_str(self):
        ns = NickSelection(123, "Gasman")
        self.assertEqual(str(ns), "Gasman")

    def test_repr(self):
        ns = NickSelection(123, "Gasman")
        self.assertEqual(repr(ns), "NickSelection: 123, Gasman")

    def test_eq(self):
        self.assertTrue(NickSelection("newscener", "Gasman") == NickSelection("newscener", "Gasman"))
        self.assertTrue(NickSelection("newgroup", "Fairlight") == NickSelection("newgroup", "Fairlight"))
        self.assertFalse(NickSelection(123, "Gasman") == NickSelection("newscener", "Gasman"))
        self.assertFalse(NickSelection("newscener", "Equinox") == NickSelection("newgroup", "Equinox"))

    def test_neq(self):
        self.assertTrue(NickSelection(123, "Gasman") != NickSelection(124, "Gasman"))
        self.assertFalse(NickSelection(123, "Raww Arse") != NickSelection(123, "RA"))


class TestMatchedNickField(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_render(self):
        class MatchedNickForm(forms.Form):
            nick = MatchedNickField(NickSearch("ra"))

        form = MatchedNickForm()
        form_html = form.as_p()
        self.assertIn('for="id_nick_id"', form_html)

    def test_clean(self):
        class MatchedNickForm(forms.Form):
            nick = MatchedNickField(NickSearch("ra"))

        form = MatchedNickForm({"nick_id": "newgroup", "nick_name": "rah"})
        self.assertFalse(form.is_valid())

        form = MatchedNickForm({"nick_id": "newgroup", "nick_name": "ra"})
        self.assertTrue(form.is_valid())

        form = MatchedNickForm({"nick_id": "1", "nick_name": "ra"})
        self.assertFalse(form.is_valid())

        form = MatchedNickForm({"nick_id": "3", "nick_name": "ra"})
        self.assertTrue(form.is_valid())


class TestNickLookup(TestCase):
    def test_eq(self):
        nl = NickLookup()
        self.assertFalse(nl == "fish")


class TestNickField(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_clean_blank(self):
        class NickForm(forms.Form):
            nick = NickField(required=False)

        form = NickForm({"nick_search": ""})
        self.assertTrue(form.is_valid())

        class RequiredNickForm(forms.Form):
            nick = NickField()

        form = RequiredNickForm({"nick_search": ""})
        self.assertFalse(form.is_valid())

    def test_clean_whitespace(self):
        class NickForm(forms.Form):
            nick = NickField(required=False)

        form = NickForm({"nick_search": "   "})
        self.assertTrue(form.is_valid())

        class RequiredNickForm(forms.Form):
            nick = NickField()

        form = RequiredNickForm({"nick_search": "   "})
        self.assertFalse(form.is_valid())

    def test_clean_autoaccept(self):
        class NickForm(forms.Form):
            nick = NickField(required=False)

        form = NickForm({"nick_search": "gasman"})
        self.assertTrue(form.is_valid())

        form = NickForm({"nick_search": "ra"})
        self.assertFalse(form.is_valid())
