from haystack.indexes import *
from haystack import site
from demoscene.models import Production, Releaser, Party

class ProductionIndex(SearchIndex):
	text = CharField(document=True, use_template=True)
site.register(Production, ProductionIndex)

class ReleaserIndex(SearchIndex):
	text = CharField(document = True, use_template = True)
site.register(Releaser, ReleaserIndex)

class PartyIndex(SearchIndex):
	text = CharField(document = True, model_attr = 'name')
site.register(Party, PartyIndex)
