from __future__ import absolute_import, unicode_literals

from django.db import transaction
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from taggit.models import Tag

from search.indexing import index


@receiver(post_save)
def on_save(sender, **kwargs):
    if not hasattr(sender, 'index_components'):
        return
    transaction.on_commit(make_updater(kwargs['instance']))


@receiver(m2m_changed)
def on_m2m_changed(sender, **kwargs):
    instance = kwargs['instance']
    model = kwargs['model']
    if model is Tag:
        transaction.on_commit(make_updater(instance))
    elif isinstance(instance, Tag):  # pragma: no cover
        # only applicable to tag relations with non-generic TaggedItem through models?
        for obj in model.objects.filter(pk__in=kwargs['pk_set']):
            if hasattr(obj, 'index_components'):
                transaction.on_commit(make_updater(obj))


def make_updater(instance):
    def on_commit():
        index(instance)

    return on_commit
