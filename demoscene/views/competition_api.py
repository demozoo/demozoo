from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.http import HttpResponse
from demoscene.models import Competition, CompetitionPlacing, Production, Nick
from byline_field import BylineLookup
import datetime

def process_row(request, competition_id, row_id = None):
	competition = get_object_or_404(Competition, id = competition_id)
	if row_id == None:
		row = CompetitionPlacing(competition = competition)
	else:
		row = get_object_or_404(CompetitionPlacing, competition = competition, id = row_id)
	
	if request.method == 'POST' or request.method == 'PUT':
		row_data = simplejson.loads(request.raw_post_data)
		new_production_id = row_data.get('production_id')
		if row.production_id != None and new_production_id != None and int(new_production_id) != row.production_id:
			# replacing production; delete previous production object if not 'stable'
			if not row.production.is_stable_for_competitions():
				row.production.delete()
		if new_production_id == None:
			# creating a new production
			new_production = Production(
				release_date_date = (competition.party.end_date_date or competition.party.start_date_date),
				release_date_precision = (competition.party.end_date_precision or competition.party.start_date_precision),
				has_bonafide_edits = False,
				updated_at = datetime.datetime.now()
			)
		else:
			new_production = Production.objects.get(id = new_production_id)
		
		new_production_data = row_data.get('production')
		if new_production_data and not new_production.is_stable_for_competitions():
			new_production.title = new_production_data['title']
			new_production.save()
			
			new_production.author_nicks = [
				Nick.from_id_and_name(nick_data['id'], nick_data['name'])
				for nick_data in new_production_data['authors']
			]
			new_production.author_affiliation_nicks = [
				Nick.from_id_and_name(nick_data['id'], nick_data['name'])
				for nick_data in new_production_data['affiliations']
			]
			if new_production_data['platform']:
				new_production.platforms = [new_production_data['platform']]
			else:
				new_production.platforms = []
				
			if new_production_data['production_type']:
				new_production.types = [new_production_data['production_type']]
			else:
				new_production.types = []
			new_production.supertype = new_production.inferred_supertype
			new_production.save()
		
		row.production = new_production
		row.ranking = row_data['ranking']
		row.position = row_data['position'] # TODO: shift other rows as required
		row.score = row_data['score']
		row.save()
	
	byline_string = unicode(row.production.byline())
	
	row_data = {
		'id': row.id,
		'position': row.position,
		'ranking': row.ranking,
		'score': row.score,
		'production_id': row.production.id,
		'production': {
			'page_url': row.production.get_absolute_url(),
			'title': row.production.title,
			'byline_string': byline_string,
			'byline_matches': BylineLookup(search_term = byline_string).render_match_fields('byline'),
		}
	}
	return HttpResponse(simplejson.dumps(row_data), mimetype="text/javascript")
