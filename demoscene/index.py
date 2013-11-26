from djapian import space, Indexer, CompositeIndexer

from demoscene.models import *
from parties.models import *


class ProductionIndexer(Indexer):
	fields = [('asciified_title', 1000), 'tags_string', 'plaintext_notes']
space.add_index(Production, ProductionIndexer, attach_as='indexer')


class ReleaserIndexer(Indexer):
	fields = [('asciified_all_names_string', 1000), ('asciified_public_real_name', 500), 'asciified_location', 'plaintext_notes']
space.add_index(Releaser, ReleaserIndexer, attach_as='indexer')


class ReleaserIndexerWithRealNames(Indexer):
	fields = [('asciified_all_names_string', 1000), ('asciified_real_name', 500), 'asciified_location', 'plaintext_notes']
space.add_index(Releaser, ReleaserIndexerWithRealNames, attach_as='indexer_with_real_names')


# TODO: index PartySeries (also platform?)

class PartyIndexer(Indexer):
	fields = [('asciified_name', 1000), 'asciified_location', ('tagline', 200), 'plaintext_notes']
space.add_index(Party, PartyIndexer, attach_as='indexer')

complete_indexer = CompositeIndexer(Production.indexer, Releaser.indexer, Party.indexer)
complete_indexer_with_real_names = CompositeIndexer(Production.indexer, Releaser.indexer_with_real_names, Party.indexer)


class ProductionNameIndexer(Indexer):
	fields = ['asciified_title']
space.add_index(Production, ProductionNameIndexer, attach_as='name_indexer')


class ReleaserNameIndexer(Indexer):
	fields = ['asciified_all_names_string', 'asciified_public_real_name']
space.add_index(Releaser, ReleaserNameIndexer, attach_as='name_indexer')


class ReleaserNameIndexerWithRealNames(Indexer):
	fields = ['asciified_all_names_string', 'asciified_real_name']
space.add_index(Releaser, ReleaserNameIndexerWithRealNames, attach_as='name_indexer_with_real_names')


class PartyNameIndexer(Indexer):
	fields = ['asciified_name', 1000]
space.add_index(Party, PartyNameIndexer, attach_as='name_indexer')

name_indexer = CompositeIndexer(Production.name_indexer, Releaser.name_indexer, Party.name_indexer)
name_indexer_with_real_names = CompositeIndexer(Production.name_indexer, Releaser.name_indexer_with_real_names, Party.name_indexer)
