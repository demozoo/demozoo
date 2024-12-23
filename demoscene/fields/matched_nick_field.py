from itertools import chain

from django import forms
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from demoscene.models import Nick

from .nick_search import NickSelection


class NickChoicesWidget(forms.RadioSelect):
    template_name = "widgets/nick_choices.html"

    def optgroups(self, name, value, attrs=None):
        groups = []
        has_selected = False

        for index, choice in enumerate(chain(self.choices)):
            # each choice is a struct of:
            # className, nameWithDifferentiator, nameWithAffiliations, countryCode, differentiator, alias, id
            option_value = choice["id"]
            option_label = self.create_label(choice)

            selected = force_str(option_value) in value and (has_selected is False or self.allow_multiple_selected)
            if selected is True and has_selected is False:
                has_selected = True
            option = self.create_option(
                name,
                option_value,
                option_label,
                selected,
                index,
                subindex=None,
                attrs=attrs,
            )
            option["classname"] = choice["className"]
            option["name_with_differentiator"] = choice["nameWithDifferentiator"]

            groups.append((None, [option], index))

        return groups

    def create_label(self, choice):
        if choice.get("countryCode"):
            flag = '<img src="/static/images/icons/flags/%s.png" data-countrycode="%s" alt="(%s)" /> ' % (
                conditional_escape(choice["countryCode"]),
                conditional_escape(choice["countryCode"]),
                conditional_escape(choice["countryCode"].upper()),
            )
        else:
            flag = ""

        if choice.get("differentiator"):
            differentiator = ' <em class="differentiator">(%s)</em>' % conditional_escape(choice["differentiator"])
        else:
            differentiator = ""

        if choice.get("alias"):
            alias = ' <em class="alias">(%s)</em>' % conditional_escape(choice["alias"])
        else:
            alias = ""

        return mark_safe(flag + choice["nameWithAffiliations"] + differentiator + alias)


class MatchedNickWidget(forms.Widget):
    def __init__(self, nick_search, attrs=None):
        self.nick_search = nick_search

        self.choices = self.nick_search.suggestions
        self.selection = self.nick_search.selection

        self.select_widget = NickChoicesWidget(choices=self.choices, attrs=attrs)
        self.name_widget = forms.HiddenInput()

        super().__init__(attrs=attrs)

    def value_from_datadict(self, data, files, name):
        nick_id = self.select_widget.value_from_datadict(data, files, name + "_id")
        nick_name = self.name_widget.value_from_datadict(data, files, name + "_name")
        if nick_id:
            return NickSelection(nick_id, nick_name)
        else:
            return None

    def id_for_label(self, id_):
        if id_:
            id_ += "_id"
        return id_

    id_for_label = classmethod(id_for_label)

    def render(self, name, value, attrs=None, renderer=None):
        selected_id = (value and value.id) or (self.selection and self.selection.id)
        output = [
            self.select_widget.render(name + "_id", selected_id, attrs=attrs, renderer=renderer),
            self.name_widget.render(name + "_name", self.nick_search.search_term, attrs=attrs, renderer=renderer),
        ]
        return mark_safe('<div class="nick_match" data-nick-match>' + "".join(output) + "</div>")


class MatchedNickField(forms.Field):
    def __init__(self, nick_search, *args, **kwargs):
        self.nick_search = nick_search

        self.widget = MatchedNickWidget(self.nick_search)

        super().__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            value = self.nick_search.selection
        elif isinstance(value, NickSelection):
            # check that it's a valid selection given the available choices
            if value.id == "newscener" or value.id == "newgroup":
                if value.name.lower() != self.nick_search.search_term.lower():  # invalid...
                    value = self.nick_search.selection  # ...so start a fresh match
            else:
                if int(value.id) not in [choice["id"] for choice in self.widget.choices]:  # invalid...
                    value = self.nick_search.selection  # ...so start a fresh match
        elif isinstance(value, Nick):  # pragma: no cover
            raise Exception("Expected NickSelection, got Nick: %r" % value)

        if isinstance(value, NickSelection) or value is None:
            return super().clean(value)
        else:  # pragma: no cover
            raise Exception("Don't know how to clean %s" % repr(value))
