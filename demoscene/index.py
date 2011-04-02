from djapian import space, Indexer, CompositeIndexer

from demoscene.models import *

class ProductionIndexer(Indexer):
	fields = [('title', 1000), ('byline_string', 50), 'plaintext_notes']
space.add_index(Production, ProductionIndexer, attach_as='indexer')

class ReleaserIndexer(Indexer):
	fields = [('all_names_string', 1000), ('public_real_name', 500), ('all_affiliation_names_string', 50), 'location', 'plaintext_notes']
space.add_index(Releaser, ReleaserIndexer, attach_as='indexer')

# TODO: index PartySeries (also platform?)

class PartyIndexer(Indexer):
	fields = [('name', 1000), 'location', 'plaintext_notes']
space.add_index(Party, PartyIndexer, attach_as='indexer')

complete_indexer = CompositeIndexer(Production.indexer, Releaser.indexer, Party.indexer)


class ProductionNameIndexer(Indexer):
	fields = ['title']
space.add_index(Production, ProductionNameIndexer, attach_as='name_indexer')

class ReleaserNameIndexer(Indexer):
	fields = ['all_names_string', 'public_real_name']
space.add_index(Releaser, ReleaserNameIndexer, attach_as='name_indexer')

class PartyNameIndexer(Indexer):
	fields = ['name', 1000]
space.add_index(Party, PartyNameIndexer, attach_as='name_indexer')

name_indexer = CompositeIndexer(Production.name_indexer, Releaser.name_indexer, Party.name_indexer)
