from piston.handler import BaseHandler
from demoscene.models import *

class ProductionHandler(BaseHandler):
	allowed_methods = ('GET',)
	fields = (
		'id', 'title', 'notes', 'supertype',
		'created_at', 'updated_at',
		('types', ('id', 'name')),
		('platforms', ('id', 'name')),
		('author_nicks', ('id', 'name', 'releaser_id')),
		('author_affiliation_nicks', ('id', 'name', 'releaser_id')),
		('download_links', ('id', 'url', 'host_identifier')),
		('credits', (
			'role',
			('nick', ('id', 'name', 'releaser_id')),
		)),
	)
	model = Production

	def read(self, request, production_id):
		return Production.objects.get(pk=production_id)
