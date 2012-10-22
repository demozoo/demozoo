import operator
import re

import xapian

from django.db import models
from django.utils.functional import curry

class X(models.Q):
    pass

i = lambda f: lambda a, b: f(a.lower(), b.lower())

startswith = lambda a, b: a.startswith(b)
endswith = lambda a, b: a.endswith(b)
regex = lambda a, b: re.match(b, a) is not None
iregex = lambda a, b: re.match(b, a, re.I) is not None

class CompositeDecider(xapian.MatchDecider):
    # operators map
    op_map = {
        'exact': operator.eq,
        'iexact': i(operator.eq),

        'startswith': startswith,
        'istartswith': i(startswith),

        'endswith': endswith,
        'iendswith': i(endswith),

        'contains': operator.contains,
        'icontains': i(operator.contains),

        'regex': regex,
        'iregex': iregex,

        'in': lambda a, b: operator.contains(b, a),
        'gt': operator.gt,
        'gte': operator.ge,
        'lt': operator.lt,
        'lte': operator.le,
    }

    def __init__(self, model, tags, filter, exclude):
        xapian.MatchDecider.__init__(self)

        self._model = model
        self._tags = tags
        self._values_map = dict([(t.prefix, t.number) for t in tags])
        self._filter = filter
        self._exclude = exclude

    def __call__(self, document):
        if self._filter and not self._do_x(self._filter, document):
            return False

        if self._exclude and self._do_x(self._exclude, document):
            return False

        return True

    def get_tag(self, index):
        for tag in self._tags:
            if tag.number == index:
                return tag
        raise ValueError("No tag with number '%s'" % index)

    def _do_x(self, field, document):
        for child in field.children:
            if isinstance(child, X):
                result = self._do_x(child, document)
            else:
                result = self._do_field(child[0], child[1], document)

            if (result and field.connector == 'OR')\
                or (not result and field.connector == 'AND'):
                break

        if field.negated:
            return not result
        else:
            return result

    def _do_field(self, lookup, value, document):
        if '__' in lookup:
            field, op = lookup.split('__', 1)
        else:
            field, op = lookup, 'exact'

        if op not in self.op_map:
            raise ValueError("Unknown lookup operator '%s'" % op)

        op = self.op_map[op]

        doc_value = document.get_value(self._values_map[field])

        convert = self.get_tag(self._values_map[field]).convert

        if isinstance(value, (list, tuple)):
            value = map(convert, value)
        else:
            value = convert(value)

        operands = [
            doc_value,
            value,
        ]

        return reduce(op, operands)
