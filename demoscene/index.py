from djapian import space, Indexer, CompositeIndexer

from demoscene.models import *

class ProductionIndexer(Indexer):
	fields = [('title', 1000), ('byline_string', 50), 'notes']
space.add_index(Production, ProductionIndexer, attach_as='indexer')

class ReleaserIndexer(Indexer):
	fields = [('all_names_string', 1000), ('public_real_name', 500), ('all_affiliation_names_string', 50), 'location', 'notes']
space.add_index(Releaser, ReleaserIndexer, attach_as='indexer')

class PartyIndexer(Indexer):
	fields = [('name', 1000), 'location', 'notes']
space.add_index(Party, PartyIndexer, attach_as='indexer')

complete_indexer = CompositeIndexer(Production.indexer, Releaser.indexer, Party.indexer)
