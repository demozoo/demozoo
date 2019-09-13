import operator
from django.contrib.postgres.search import SearchVector
from django.db.models import Value


def index(instance):
    pk = instance.pk
    components = instance.index_components()
    try:
        admin_components = instance.admin_index_components()
    except AttributeError:
        admin_components = None

    search_vectors = []
    for weight, text in components.items():
        search_vectors.append(
            SearchVector(Value(text), weight=weight)
        )
    if admin_components:
        admin_search_vectors = []
        for weight, text in admin_components.items():
            admin_search_vectors.append(
                SearchVector(Value(text), weight=weight)
            )
        instance.__class__.objects.filter(pk=pk).update(
            search_document=reduce(operator.add, search_vectors),
            admin_search_document=reduce(operator.add, admin_search_vectors),
        )
    else:
        instance.__class__.objects.filter(pk=pk).update(
            search_document=reduce(operator.add, search_vectors)
        )
