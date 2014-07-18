from itertools import groupby

from django.http import HttpResponse
from django.utils import simplejson

from demoscene.models import ReleaserExternalLink
from productions.models import Credit, ProductionLink
from parties.models import PartyExternalLink


def credits(request):
	# Retrieve productions with Pouet IDs with credits for releasers who have Pouet user IDs
	credits = Credit.objects.raw('''
		SELECT
			productions_credit.id,
			productions_productionlink.parameter AS pouet_prod_id,
			demoscene_releaserexternallink.parameter AS pouet_user_id,
			productions_credit.category,
			productions_credit.role
		FROM
			productions_credit
			INNER JOIN productions_productionlink ON (
				productions_credit.production_id = productions_productionlink.production_id
				AND productions_productionlink.link_class = 'PouetProduction'
			)
			INNER JOIN demoscene_nick ON (
				productions_credit.nick_id = demoscene_nick.id
			)
			INNER JOIN demoscene_releaserexternallink ON (
				demoscene_nick.releaser_id = demoscene_releaserexternallink.releaser_id
				AND demoscene_releaserexternallink.link_class = 'SceneidAccount'
			)
		ORDER BY
			pouet_prod_id, pouet_user_id, category
	''')

	credits_json = [
		{
			'pouet_prod_id': prod_id,
			'pouet_user_id': user_id,
			'role': ', '.join([
				("%s (%s)" % (cred.category, cred.role)) if cred.role else cred.category
				for cred in creds
			]),
		}
		for ((prod_id, user_id), creds) in groupby(credits, lambda c: (c.pouet_prod_id, c.pouet_user_id))
	]

	return HttpResponse(simplejson.dumps(credits_json), mimetype="text/javascript")


def prod_demozoo_ids_by_pouet_id(request):
	links = ProductionLink.objects.filter(link_class='PouetProduction')
	links_json = [
		{'pouet_id': int(link.parameter), 'demozoo_id': link.production_id}
		for link in links
	]
	return HttpResponse(simplejson.dumps(links_json), mimetype="text/javascript")


def prod_demozoo_ids_by_zxdemo_id(request):
	links = ProductionLink.objects.filter(link_class='ZxdemoItem')
	links_json = [
		{'zxdemo_id': int(link.parameter), 'demozoo_id': link.production_id}
		for link in links
	]
	return HttpResponse(simplejson.dumps(links_json), mimetype="text/javascript")


def group_demozoo_ids_by_pouet_id(request):
	links = ReleaserExternalLink.objects.filter(link_class='PouetGroup')
	links_json = [
		{'pouet_id': int(link.parameter), 'demozoo_id': link.releaser_id}
		for link in links
	]
	return HttpResponse(simplejson.dumps(links_json), mimetype="text/javascript")


def group_demozoo_ids_by_zxdemo_id(request):
	links = ReleaserExternalLink.objects.filter(link_class='ZxdemoAuthor')
	links_json = [
		{'zxdemo_id': int(link.parameter), 'demozoo_id': link.releaser_id}
		for link in links
	]
	return HttpResponse(simplejson.dumps(links_json), mimetype="text/javascript")


def party_demozoo_ids_by_pouet_id(request):
	links = PartyExternalLink.objects.filter(link_class='PouetParty')
	links_json = []
	for link in links:
		party_id, year = link.parameter.split('/')
		links_json.append({
			'pouet_id': int(party_id), 'year': int(year),
			'demozoo_id': link.party_id
		})
	return HttpResponse(simplejson.dumps(links_json), mimetype="text/javascript")


def party_demozoo_ids_by_zxdemo_id(request):
	links = PartyExternalLink.objects.filter(link_class='ZxdemoParty')
	links_json = [
		{'zxdemo_id': int(link.parameter), 'demozoo_id': link.party_id}
		for link in links
	]
	return HttpResponse(simplejson.dumps(links_json), mimetype="text/javascript")
