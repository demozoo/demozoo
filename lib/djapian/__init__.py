from django.conf import settings

from djapian.indexer import Field, Indexer, CompositeIndexer
from djapian.database import Database
from djapian.space import IndexSpace
from djapian.utils import load_indexes
from djapian.decider import X

space = IndexSpace(settings.DJAPIAN_DATABASE_PATH, "global")

add_index = space.add_index
