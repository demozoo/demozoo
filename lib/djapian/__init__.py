from django.conf import settings

from .indexer import Field, Indexer, CompositeIndexer  # noqa
from .database import Database  # noqa
from .space import IndexSpace
from .utils import load_indexes  # noqa
from .decider import X  # noqa

space = IndexSpace(settings.DJAPIAN_DATABASE_PATH, "global")

add_index = space.add_index
default_app_config = 'djapian.apps.DjapianConfig'
