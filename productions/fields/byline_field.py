from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from matched_nick_field import MatchedNickField
from submit_button_field import SubmitButtonInput

from demoscene.utils.nick_search import BylineSearch
from productions.models import Byline


# An object which encapsulates the state of a BylineWidget as derived from its posted data;
# this is what BylineWidget returns from value_from_datadict
class BylineLookup():
    def __init__(self,
        byline_search,
        author_nick_selections=[],
        affiliation_nick_selections=[],
        author_matched_nick_fields=None,
        affiliation_matched_nick_fields=None,
        autoaccept=False):

        if author_matched_nick_fields == None:
            author_matched_nick_fields = [
                MatchedNickField(nick_search, required=False)
                for nick_search in byline_search.author_nick_searches
            ]

        if affiliation_matched_nick_fields == None:
            affiliation_matched_nick_fields = [
                MatchedNickField(nick_search, required=False)
                for nick_search in byline_search.affiliation_nick_searches
            ]

        self.byline_search = byline_search
        self.autoaccept = autoaccept  # whether we should continue upon successfully resolving
            # all byline components, as opposed to re-showing the form
        self.author_nick_selections = author_nick_selections
        self.affiliation_nick_selections = affiliation_nick_selections
        self.author_matched_nick_fields = author_matched_nick_fields
        self.affiliation_matched_nick_fields = affiliation_matched_nick_fields

    @property
    def search_term(self):
        return self.byline_search.search_term

    def render_match_fields(self, name, attrs={}, renderer=None):
        match_html_output = []

        for i, field in enumerate(self.author_matched_nick_fields):
            field_name = name + ('_author_match_%s' % i)
            try:
                html = field.widget.render(
                    field_name, self.author_nick_selections[i], attrs=attrs, renderer=renderer
                )
            except IndexError:
                html = field.widget.render(field_name, None, attrs=attrs, renderer=renderer)
            match_html_output.append(html)

        for i, field in enumerate(self.affiliation_matched_nick_fields):
            field_name = name + ('_affiliation_match_%s' % i)
            try:
                html = field.widget.render(
                    field_name, self.affiliation_nick_selections[i], attrs=attrs, renderer=renderer
                )
            except IndexError:
                html = field.widget.render(field_name, None, attrs=attrs, renderer=renderer)
            match_html_output.append(html)

        return u''.join(match_html_output)

    @staticmethod
    def from_value(value):
        # value can be:
        # a Byline
        # a BylineSearch
        # None
        # an existing BylineLookup
        if not value:
            return BylineLookup(byline_search=BylineSearch(''))
        elif isinstance(value, BylineLookup):
            return value  # BylineLookups are treated as immutable, so it's safe to return the initial instance
        elif isinstance(value, BylineSearch):
            return BylineLookup(
                byline_search=value,
                author_nick_selections=value.author_nick_selections,
                affiliation_nick_selections=value.affiliation_nick_selections)
        elif isinstance(value, Byline):  # TODO: can we eliminate Byline here in favour of BylineSearch?
            byline_search = BylineSearch.from_byline(value)
            return BylineLookup(
                byline_search=byline_search,
                author_nick_selections=byline_search.author_nick_selections,
                affiliation_nick_selections=byline_search.affiliation_nick_selections)
        else:
            raise ValidationError("Don't know how to handle %s as a byline lookup" % repr(value))

    def __repr__(self):
        return "<BylineLookup: %s, %s>" % (repr(self.author_nick_selections), repr(self.affiliation_nick_selections))

    def __eq__(self, other):
        if not isinstance(other, BylineLookup):
            return False
        return self.author_nick_selections == other.author_nick_selections and self.affiliation_nick_selections == other.affiliation_nick_selections

    def __ne__(self, other):
        return not self.__eq__(other)


class BylineWidget(forms.Widget):
    def __init__(self, attrs=None):
        self.search_widget = forms.TextInput(attrs=attrs)
        self.lookup_widget = SubmitButtonInput(button_text='Find names')
        super(BylineWidget, self).__init__(attrs=attrs)

    def value_from_datadict(self, data, files, name):
        search_term = self.search_widget.value_from_datadict(data, files, name + '_search')
        if not search_term:
            return None

        explicit_lookup_requested = self.lookup_widget.value_from_datadict(data, files, name + '_lookup')

        byline_search = BylineSearch(search_term)
        # byline_search now has the appropriate number of author_nick_searches and affiliation_nick_searches
        # for the passed search term; we can use that to construct the right number of MatchedNickFields

        author_matched_nick_fields = [
            MatchedNickField(nick_search, required=False)
            for nick_search in byline_search.author_nick_searches
        ]
        affiliation_matched_nick_fields = [
            MatchedNickField(nick_search, required=False)
            for nick_search in byline_search.affiliation_nick_searches
        ]

        # we can now use those MatchedNickFields to extract the NickSelections from the form submission -
        # unless explicit_lookup_requested is set, in which case those selections are discarded
        if explicit_lookup_requested:
            author_nick_selections = []
            affiliation_nick_selections = []
        else:
            author_nick_selections = [
                field.widget.value_from_datadict(data, files, name + ('_author_match_%s' % i))
                for i, field in enumerate(author_matched_nick_fields)
            ]
            affiliation_nick_selections = [
                field.widget.value_from_datadict(data, files, name + ('_affiliation_match_%s' % i))
                for i, field in enumerate(affiliation_matched_nick_fields)
            ]

        return BylineLookup(
            byline_search=byline_search,
            author_matched_nick_fields=author_matched_nick_fields,
            affiliation_matched_nick_fields=affiliation_matched_nick_fields,
            author_nick_selections=author_nick_selections,
            affiliation_nick_selections=affiliation_nick_selections,
            autoaccept=not explicit_lookup_requested)

    def id_for_label(self, id_):
        if id_:
            id_ += '_search'
        return id_
    id_for_label = classmethod(id_for_label)

    def render(self, name, value, attrs=None, renderer=None):
        byline_lookup = BylineLookup.from_value(value)

        search_attrs = self.build_attrs(attrs)
        search_attrs['id'] += '_search'
        lookup_attrs = self.build_attrs(attrs)
        lookup_attrs['id'] += '_lookup'

        search_html_output = [
            self.search_widget.render(
                name + '_search', byline_lookup.search_term, attrs=search_attrs, renderer=renderer
            ),
            self.lookup_widget.render(
                name + '_lookup', None, attrs=lookup_attrs, renderer=renderer
            ),
        ]

        if byline_lookup.search_term:
            matched_nick_html = byline_lookup.render_match_fields(name, renderer=renderer)
        else:
            matched_nick_html = ''

        output = [
            u'<div class="byline_search">' + u''.join(search_html_output) + u'</div>',
            u'<div class="byline_match_container">' + matched_nick_html + u'</div>'
        ]

        root_classname = u'byline_field'
        return mark_safe(u'<div class="' + root_classname + u'">' + u''.join(output) + u'</div>')


class BylineField(forms.Field):
    def __init__(self, *args, **kwargs):
        self.widget = BylineWidget()
        super(BylineField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            # pass on to Field to handle null value according to the 'blank' parameter
            return super(BylineField, self).clean(value)
        else:
            byline_lookup = BylineLookup.from_value(value)

            clean_author_nick_selections = []
            clean_affiliation_nick_selections = []
            if byline_lookup.autoaccept:
                validation_message = "Not all names could be matched to a scener or group; please select the appropriate ones from the lists."
            else:
                validation_message = "Please select the appropriate sceners / groups from the lists."

            for i, field in enumerate(byline_lookup.author_matched_nick_fields):
                try:
                    value = byline_lookup.author_nick_selections[i]
                except IndexError:
                    raise ValidationError(validation_message)
                clean_value = field.clean(value)
                if not clean_value:
                    raise ValidationError(validation_message)
                clean_author_nick_selections.append(clean_value)

            for i, field in enumerate(byline_lookup.affiliation_matched_nick_fields):
                try:
                    value = byline_lookup.affiliation_nick_selections[i]
                except IndexError:  # pragma: no cover
                    raise ValidationError(validation_message)
                clean_value = field.clean(value)
                if not clean_value:
                    raise ValidationError(validation_message)
                clean_affiliation_nick_selections.append(clean_value)

            return Byline(
                clean_author_nick_selections, clean_affiliation_nick_selections)

    def has_changed(self, initial, data):
        initial = BylineLookup.from_value(initial)
        data = BylineLookup.from_value(data)
        return initial != data
