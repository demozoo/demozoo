from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.http import HttpResponse
from demoscene.models import Competition, CompetitionPlacing, Production, Nick, Platform, ProductionType
from byline_field import BylineLookup
from matched_nick_field import NickSelection
from django.contrib.auth.decorators import login_required
from django.db.models import F
import datetime

# helper function: create or update a production according to JSON data
def handle_production(prod_data):
	if prod_data.get('id'):
		production = Production.objects.get(id = prod_data['id'])
	else:
		production = Production(updated_at = datetime.datetime.now(), has_bonafide_edits = False)
		# TODO: populate release date by competition
		production.save() # assign an ID so that associations work
	
	# can only edit production details if production is stable (which is always true for
	# newly-created ones)
	if not production.is_stable_for_competitions():
		if 'title' in prod_data:
			production.title = prod_data['title']
		if 'platform_id' in prod_data:
			if prod_data['platform_id']:
				production.platforms = [Platform.objects.get(id = prod_data['platform_id'])]
			else:
				production.platforms = []
		if 'production_type_id' in prod_data:
			if prod_data['production_type_id']:
				production.types = [ProductionType.objects.get(id = prod_data['production_type_id'])]
			else:
				production.types = []
		if 'byline' in prod_data:
			production.author_nicks = [
				NickSelection(author['id'], author['name']).commit()
				for author in prod_data['byline']['authors']
			]
			production.author_affiliation_nicks = [
				NickSelection(affillation['id'], affillation['name']).commit()
				for affillation in prod_data['byline']['affiliations']
			]
		production.updated_at = datetime.datetime.now()
		production.supertype = production.inferred_supertype
		production.save()
		
	return production

@login_required
def add_placing(request, competition_id):
	competition = get_object_or_404(Competition, id = competition_id)
	if request.method == 'POST':
		data = simplejson.loads(request.raw_post_data)
		
		# move existing placings to accommodate new entry at the stated position
		competition.placings.filter(position__gt = data['position']).update(position=F('position') + 1)
		
		placing = CompetitionPlacing(
			production = handle_production(data['production']),
			competition = competition,
			ranking = data['ranking'],
			position = data['position'],
			score = data['score']
		)
		placing.save()
		
		return HttpResponse(simplejson.dumps(placing.json_data), mimetype="text/javascript")

@login_required
def update_placing(request, placing_id):
	placing = get_object_or_404(CompetitionPlacing, id = placing_id)
	competition = placing.competition
	if request.method == 'POST':
		data = simplejson.loads(request.raw_post_data)
		
		# move existing placings to accommodate new entry at the stated position
		if int(data['position']) > placing.position: # increasing position - move others down
			competition.placings.filter(position__gt = placing.position, position__lte = data['position']).update(position=F('position') - 1)
		elif int(data['position']) < placing.position: # decreasing position - move others up
			competition.placings.filter(position__gte = data['position'], position__lt = placing.position).update(position=F('position') + 1)
		
		placing.production = handle_production(data['production'])
		placing.ranking = data['ranking']
		placing.position = data['position']
		placing.score = data['score']
		placing.save()
		
		return HttpResponse(simplejson.dumps(placing.json_data), mimetype="text/javascript")

@login_required
def delete_placing(request, placing_id):
	placing = get_object_or_404(CompetitionPlacing, id = placing_id)
	competition = placing.competition
	if request.method == 'POST':
		# Delete production entry too, if it wasn't stable; need to do this test before deleting
		# the placing, as number of placings is one criterion for whether it's stable or not
		delete_production_too = not placing.production.is_stable_for_competitions()
		placing.delete()
		# move remaining placings to close the gap
		competition.placings.filter(position__gt = placing.position).update(position=F('position') - 1)
		if delete_production_too:
			placing.production.delete()
		
		return HttpResponse('OK', mimetype="text/plain")

# --- old api ---

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
