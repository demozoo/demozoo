from django.apps import AppConfig
from django.utils.translation import ugeettext_lazy as _


class DjapianConfig(AppConfig):
    name = 'djapian'
    verbose_name = _("Djapian")

    def ready(self):
        from django.db import models
        from .signals import post_save, pre_delete
        models.signals.post_save.connect(post_save, sender=self._model)
        models.signals.pre_delete.connect(pre_delete, sender=self._model)


