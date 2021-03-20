from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'search'

    def ready(self):
        # import signal handlers
        from search import signals  # noqa
