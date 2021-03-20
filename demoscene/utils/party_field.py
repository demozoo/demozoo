from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from submit_button_field import SubmitButtonInput

from parties.models import Party


# a form field for selecting a party, e.g. in the 'invitation for...' field on a production form

# An object which encapsulates the state of a PartyWidget as derived from its posted data;
# this is what PartyWidget returns from value_from_datadict
class PartyLookup():
    def __init__(self, search_term=None, party_id=None, redisplay=False):

        self.search_term = search_term  # the party name being looked up
        self.party_id = party_id  # the party ID previously chosen (cached in a hidden field)

        # whether we should redisplay the form even if we've successfully resolved the input to a party
        self.redisplay = redisplay

        self.validation_error = None
        self.is_empty = False
        self.party = None
        if self.redisplay:
            # force a redisplay of the form; i.e. produce a ValidationError whatever happens
            if not self.search_term:
                self.validation_error = ValidationError("No party selected")
            else:
                # look for a party matching the search term
                try:
                    self.party = Party.objects.get(name__iexact=self.search_term)
                    self.party_id = self.party.id
                    self.validation_error = ValidationError("Party '%s' found." % self.party.name)
                except Party.DoesNotExist:
                    self.validation_error = ValidationError("No match found for '%s'" % self.search_term)
        else:
            if not self.search_term:
                self.is_empty = True
            else:
                if self.party_id is not None and self.party_id != '':
                    try:
                        self.party = Party.objects.get(id=self.party_id)
                    except Party.DoesNotExist:
                        pass

                if self.party is None or self.party.name != self.search_term:
                    # look for a party matching the search term
                    try:
                        self.party = Party.objects.get(name__iexact=self.search_term)
                        self.party_id = self.party.id
                    except Party.DoesNotExist:
                        self.validation_error = ValidationError("No match found for '%s'" % self.search_term)

    def validate(self):
        if self.validation_error:
            raise self.validation_error

    def commit(self):
        return self.party

    def __repr__(self):
        return "PartyLookup: %s, %s" % (repr(self.party_id), self.search_term)

    def __eq__(self, other):
        if not isinstance(other, PartyLookup):
            return False
        return self.search_term == other.search_term and str(self.party_id) == str(other.party_id)

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_value(value):
        # value can be:
        # a Party
        # None
        # an existing PartyLookup
        if not value:
            return PartyLookup()
        elif isinstance(value, PartyLookup):
            return PartyLookup(search_term=value.search_term, party_id=value.party_id, redisplay=value.redisplay)
        elif isinstance(value, Party):
            return PartyLookup(search_term=value.name, party_id=value.id, redisplay=False)
        else:
            raise ValidationError("Don't know how to handle %s as a party lookup" % repr(value))


class PartyWidget(forms.Widget):
    def __init__(self, attrs=None):
        self.search_widget = forms.TextInput(attrs={'class': 'party_field_search'})
        self.lookup_widget = SubmitButtonInput(button_text='Find party', attrs={'class': 'party_field_lookup'})
        self.party_id_widget = forms.HiddenInput(attrs={'class': 'party_field_party_id'})
        super(PartyWidget, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None, renderer=None):
        party_lookup = PartyLookup.from_value(value)

        output = [
            self.search_widget.render(
                name + '_search', party_lookup.search_term, attrs=attrs, renderer=None
            ),
            self.lookup_widget.render(name + '_lookup', None, attrs=attrs, renderer=None),
            self.party_id_widget.render(
                name + '_party_id', party_lookup.party_id, attrs=attrs, renderer=None
            ),
            '<div class="help_text">(if the party doesn\'t exist yet, '
            '<a href="/parties/new/" target="_blank">create it first</a>!)</div>'
        ]

        return mark_safe(u'<div class="party_field">' + u''.join(output) + u'</div>')

    def value_from_datadict(self, data, files, name):
        search_term = self.search_widget.value_from_datadict(data, files, name + '_search')
        redisplay = self.lookup_widget.value_from_datadict(data, files, name + '_lookup')
        party_id = self.party_id_widget.value_from_datadict(data, files, name + '_party_id')

        party_lookup = PartyLookup(search_term=search_term, redisplay=redisplay, party_id=party_id)

        if party_lookup.is_empty:
            return None
        else:
            return party_lookup


class PartyField(forms.Field):
    widget = PartyWidget

    def clean(self, value):
        if value is None:
            return super(PartyField, self).clean(value)
        else:
            # if the value has come from a form submission, it will already be a PartyLookup
            # (and therefore party_lookup.redisplay will be meaningful).
            # If it has come from an 'initial' value, it will be a party object.
            party_lookup = PartyLookup.from_value(value)

            party_lookup.validate()
            return party_lookup

    def has_changed(self, initial, data):
        initial = PartyLookup.from_value(initial)
        data = PartyLookup.from_value(data)
        return data != initial
