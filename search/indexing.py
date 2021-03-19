from __future__ import absolute_import, unicode_literals

import operator
from functools import reduce

from django.contrib.postgres.search import SearchVector
from django.db.models import TextField, Value


def index(instance):
    pk = instance.pk
    components = instance.index_components()

    search_vectors = []
    for weight, text in components.items():
        search_vectors.append(
            SearchVector(Value(text, output_field=TextField()), weight=weight)
        )
    instance.__class__.objects.filter(pk=pk).update(
        search_document=reduce(operator.add, search_vectors)
    )
