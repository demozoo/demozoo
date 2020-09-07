from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase

from demoscene.utils.nick_search import NickSearch, NickSelection
from demoscene.utils.party_field import PartyField, PartyLookup
from matched_nick_field import MatchedNickField
from nick_field import NickField, NickLookup
from submit_button_field import SubmitButtonField


class TestNickSelection(TestCase):
    def test_str(self):
        ns = NickSelection(123, 'Gasman')
        self.assertEqual(str(ns), 'Gasman')

    def test_repr(self):
        ns = NickSelection(123, 'Gasman')
        self.assertEqual(repr(ns), 'NickSelection: 123, Gasman')

    def test_eq(self):
        self.assertTrue(NickSelection('newscener', 'Gasman') == NickSelection('newscener', 'Gasman'))
        self.assertTrue(NickSelection('newgroup', 'Fairlight') == NickSelection('newgroup', 'Fairlight'))
        self.assertFalse(NickSelection(123, 'Gasman') == NickSelection('newscener', 'Gasman'))
        self.assertFalse(NickSelection('newscener', 'Equinox') == NickSelection('newgroup', 'Equinox'))

    def test_neq(self):
        self.assertTrue(NickSelection(123, 'Gasman') != NickSelection(124, 'Gasman'))
        self.assertFalse(NickSelection(123, 'Raww Arse') != NickSelection(123, 'RA'))


class TestPartyLookup(TestCase):
    def test_repr(self):
        pl = PartyLookup(party_id=123, search_term='Revision 2020')
        self.assertEqual(repr(pl), 'PartyLookup: 123, Revision 2020')

    def test_eq(self):
        pl = PartyLookup(party_id=123, search_term='Revision 2020')
        self.assertFalse(pl == 'fish')

    def test_from_value(self):
        with self.assertRaises(ValidationError):
            PartyLookup.from_value('fish')


class TestPartyField(TestCase):
    def test_clean(self):
        class PartyForm(forms.Form):
            party = PartyField(required=False)

        form = PartyForm({'party_search': '', 'party_party_id': ''})
        self.assertTrue(form.is_valid())


class TestMatchedNickField(TestCase):
    fixtures = ['tests/gasman.json']

    def test_render(self):
        class MatchedNickForm(forms.Form):
            nick = MatchedNickField(NickSearch('ra'))

        form = MatchedNickForm()
        form_html = form.as_p()
        self.assertIn('for="id_nick_id"', form_html)

    def test_clean(self):
        class MatchedNickForm(forms.Form):
            nick = MatchedNickField(NickSearch('ra'))

        form = MatchedNickForm({'nick_id': 'newgroup', 'nick_name': 'rah'})
        self.assertFalse(form.is_valid())

        form = MatchedNickForm({'nick_id': 'newgroup', 'nick_name': 'ra'})
        self.assertTrue(form.is_valid())

        form = MatchedNickForm({'nick_id': '1', 'nick_name': 'ra'})
        self.assertFalse(form.is_valid())

        form = MatchedNickForm({'nick_id': '3', 'nick_name': 'ra'})
        self.assertTrue(form.is_valid())


class TestNickLookup(TestCase):
    def test_eq(self):
        nl = NickLookup()
        self.assertFalse(nl == 'fish')


class TestNickField(TestCase):
    fixtures = ['tests/gasman.json']

    def test_clean_blank(self):
        class NickForm(forms.Form):
            nick = NickField(required=False)

        form = NickForm({'nick_search': ''})
        self.assertTrue(form.is_valid())

    def test_clean_autoaccept(self):
        class NickForm(forms.Form):
            nick = NickField(required=False)

        form = NickForm({'nick_search': 'gasman'})
        self.assertTrue(form.is_valid())

        form = NickForm({'nick_search': 'ra'})
        self.assertFalse(form.is_valid())


class TestSubmitButtonField(TestCase):
    def test_val(self):
        class SubmittableForm(forms.Form): 
            lookup = SubmitButtonField(button_text='Look up name')

        form = SubmittableForm({})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['lookup'], False)

        form = SubmittableForm({'lookup': "Look up name"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['lookup'], True)

    def test_render(self):
        button = SubmitButtonField(button_text='Look up name')
        html = button.widget.render('lookup', None)
        self.assertIn("Look up name", html)
