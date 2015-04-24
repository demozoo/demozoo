import json

from django.http import HttpResponse

from demoscene.models import ReleaserExternalLink
from productions.models import ProductionLink
from parties.models import PartyExternalLink


def prod_demozoo_ids_by_zxdemo_id(request):
	links = ProductionLink.objects.filter(link_class='ZxdemoItem')
	links_json = [
		{'zxdemo_id': int(link.parameter), 'demozoo_id': link.production_id}
		for link in links
	]
	return HttpResponse(json.dumps(links_json), mimetype="text/javascript")


def group_demozoo_ids_by_zxdemo_id(request):
	links = ReleaserExternalLink.objects.filter(link_class='ZxdemoAuthor')
	links_json = [
		{'zxdemo_id': int(link.parameter), 'demozoo_id': link.releaser_id}
		for link in links
	]
	return HttpResponse(json.dumps(links_json), mimetype="text/javascript")


def party_demozoo_ids_by_zxdemo_id(request):
	links = PartyExternalLink.objects.filter(link_class='ZxdemoParty')
	links_json = [
		{'zxdemo_id': int(link.parameter), 'demozoo_id': link.party_id}
		for link in links
	]
	return HttpResponse(json.dumps(links_json), mimetype="text/javascript")
