from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase

from parties.fields import PartyField, PartyLookup


class TestPartyLookup(TestCase):
    def test_repr(self):
        pl = PartyLookup(party_id=123, search_term="Revision 2020")
        self.assertEqual(repr(pl), "PartyLookup: 123, Revision 2020")

    def test_eq(self):
        pl = PartyLookup(party_id=123, search_term="Revision 2020")
        self.assertFalse(pl == "fish")

    def test_from_value(self):
        with self.assertRaises(ValidationError):
            PartyLookup.from_value("fish")


class TestPartyField(TestCase):
    def test_clean(self):
        class PartyForm(forms.Form):
            party = PartyField(required=False)

        form = PartyForm({"party_search": "", "party_party_id": ""})
        self.assertTrue(form.is_valid())
