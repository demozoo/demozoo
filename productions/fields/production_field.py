from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.encoding import python_2_unicode_compatible
from productions.models import Production, ProductionType
import datetime
from productions.fields.byline_field import BylineField, BylineWidget
from productions.fields.production_type_field import ProductionTypeChoiceField


# A value encapsulating the state of the ProductionWidget.
# Used as the cleaned value of a ProductionField
# and the value ProductionWidget returns from value_from_datadict.
@python_2_unicode_compatible
class ProductionSelection(object):
    def __init__(self, id=None, title=None, byline_lookup=None, types_to_set=[]):
        self.id = id
        self.types_to_set = types_to_set
        if self.id:
            self.production = Production.objects.get(id=self.id)
            self.title = self.production.title
            self.byline = self.production.byline()
            self.byline_lookup = None
        else:
            self.production = None
            self.title = title
            self.byline_lookup = byline_lookup

    def commit(self):
        if not self.production:
            self.production = Production(
                title=self.title,
                updated_at=datetime.datetime.now(),
            )
            # Ugh. We really ought to come up with a nice way of setting supertype
            # in advance of setting types, rather than having to save a second time
            # once the types are in place...
            self.production.save()
            self.production.types = self.types_to_set
            self.production.save()
            if self.byline:
                self.byline.commit(self.production)
        return self.production

    def __str__(self):
        return u"ProductionSelection: %s - %s" % (self.id, self.title)

    def __eq__(self, other):
        if not isinstance(other, ProductionSelection):
            return False
        return self.title == other.title and str(self.id) == str(other.id) and self.byline_lookup == other.byline_lookup

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_value(value, types_to_set=[]):
        # value can be:
        # a Production
        # None
        # an integer (will be used as an ID)
        # an existing ProductionSelection
        if not value:
            return ProductionSelection()
        elif isinstance(value, ProductionSelection):
            return ProductionSelection(id=value.id, title=value.title, byline_lookup=value.byline_lookup, types_to_set=value.types_to_set)
        elif isinstance(value, int):
            return ProductionSelection(id=value)
        elif isinstance(value, Production):
            return ProductionSelection(id=value.id)
        else:
            raise ValidationError("Don't know how to convert %s to a ProductionSelection!" % repr(value))


class ProductionWidget(forms.Widget):
    def __init__(self, attrs=None, types_to_set=[], supertype=None, show_production_type_field=False):
        self.id_widget = forms.HiddenInput()
        self.title_widget = forms.TextInput()
        self.byline_widget = BylineWidget()
        self.types_to_set = types_to_set
        self.supertype = supertype
        self.production_type_widget = ProductionTypeChoiceField(queryset=ProductionType.objects.all()).widget
        self.show_production_type_field = show_production_type_field
        super(ProductionWidget, self).__init__(attrs=attrs)

    def value_from_datadict(self, data, files, name):
        id = self.id_widget.value_from_datadict(data, files, name + '_id')
        title = self.title_widget.value_from_datadict(data, files, name + '_title')
        byline_lookup = self.byline_widget.value_from_datadict(data, files, name + '_byline')
        if self.show_production_type_field:
            type_to_set = self.production_type_widget.value_from_datadict(data, files, name + '_type')
            if type_to_set:
                types_to_set = [ProductionType.objects.get(id=type_to_set)]
            else:
                types_to_set = []
        else:
            types_to_set = self.types_to_set

        if id or title:
            return ProductionSelection(
                id=id,
                title=title,
                byline_lookup=byline_lookup,
                types_to_set=types_to_set,
            )
        else:
            return None

    def render(self, name, value, attrs=None):
        production_selection = ProductionSelection.from_value(value, types_to_set=self.types_to_set)
        production_id = production_selection.id

        if production_id:
            byline_text = production_selection.production.byline().__unicode__()
            if byline_text:
                static_view = [
                    # FIXME: HTMLencode
                    "<b>%s</b> by %s" % (production_selection.production.title, byline_text)
                ]
            else:
                static_view = [
                    "<b>%s</b>" % production_selection.production.title
                ]
        else:
            static_view = []

        title_attrs = self.build_attrs(attrs)
        title_attrs['class'] = 'title_field'
        if self.supertype:
            title_attrs['data-supertype'] = self.supertype
        byline_attrs = self.build_attrs(attrs)
        byline_attrs['id'] += '_byline'

        prodtype_attrs = self.build_attrs(attrs)
        prodtype_attrs['id'] += '_type'

        form_view = [
            self.id_widget.render(name + '_id', production_id),
            self.title_widget.render(name + '_title', '', attrs=title_attrs),
            ' <label for="%s">by</label> ' % self.byline_widget.id_for_label('id_' + name + '_byline'),
            self.byline_widget.render(name + '_byline', '', attrs=byline_attrs),
        ]
        if self.show_production_type_field:
            form_view += [
                '<label for="%s">Type:</label> ' % self.production_type_widget.id_for_label('id_' + name + '_type'),
                self.production_type_widget.render(name + '_type', '', attrs=prodtype_attrs)
            ]

        output = [
            '<div class="production_field">',
            '<div class="static_view">',
            '<div class="static_view_text">',
            u''.join(static_view),
            '</div>',
            '</div>',
            '<div class="form_view">',
            u''.join(form_view),
            '</div>',
            '</div>',
        ]
        return mark_safe(u''.join(output))


class ProductionField(forms.Field):
    def __init__(self, *args, **kwargs):
        self.types_to_set = kwargs.pop('types_to_set', [])
        self.show_production_type_field = kwargs.pop('show_production_type_field', False)
        self.byline_field = BylineField(required=False)
        supertype = kwargs.pop('supertype', None)
        self.widget = ProductionWidget(
            types_to_set=self.types_to_set,
            supertype=supertype,
            show_production_type_field=self.show_production_type_field,
        )

        super(ProductionField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            value = None
        else:
            value = ProductionSelection.from_value(value, types_to_set=self.types_to_set)
            value.byline = self.byline_field.clean(value.byline_lookup)

        return super(ProductionField, self).clean(value)

    def has_changed(self, initial, data):
        initial = ProductionSelection.from_value(initial)
        data = ProductionSelection.from_value(data)
        return data != initial
