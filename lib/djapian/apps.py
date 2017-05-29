from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DjapianConfig(AppConfig):
    name = 'djapian'
    verbose_name = _("Djapian")

    def ready(self):
        from django.db import models
        from .signals import post_save, pre_delete
        from .utils import load_indexes
        load_indexes()
