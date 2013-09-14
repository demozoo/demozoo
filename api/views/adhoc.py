from django.utils import simplejson
from django.http import HttpResponse
from demoscene.models import Credit

from itertools import groupby

def pouet_credits(request):
	# Retrieve productions with Pouet IDs with credits for releasers who have Pouet user IDs
	credits = Credit.objects.raw('''
		SELECT
			demoscene_credit.id,
			demoscene_productionlink.parameter AS pouet_prod_id,
			demoscene_releaserexternallink.parameter AS pouet_user_id,
			demoscene_credit.category,
			demoscene_credit.role
		FROM
			demoscene_credit
			INNER JOIN demoscene_productionlink ON (
				demoscene_credit.production_id = demoscene_productionlink.production_id
				AND demoscene_productionlink.link_class = 'PouetProduction'
			)
			INNER JOIN demoscene_nick ON (
				demoscene_credit.nick_id = demoscene_nick.id
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
