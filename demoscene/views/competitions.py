from demoscene.shortcuts import *
from demoscene.models import Competition, CompetitionPlacing, Edit

from unjoinify import unjoinify


def show(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)

	columns = [
		'id',
		'ranking',
		'score',
		'production__id',
		'production__title',
		'production__supertype',
		'production__unparsed_byline',
		'production__author_nicks__id',
		'production__author_nicks__name',
		'production__author_nicks__releaser__id',
		'production__author_nicks__releaser__is_group',
		'production__author_affiliation_nicks__id',
		'production__author_affiliation_nicks__name',
		'production__author_affiliation_nicks__releaser__id',
		'production__author_affiliation_nicks__releaser__is_group',
	]
	query = '''
		SELECT
			demoscene_competitionplacing.id AS id,
			demoscene_competitionplacing.ranking AS ranking,
			demoscene_competitionplacing.score AS score,
			demoscene_production.id AS production__id,
			demoscene_production.title AS production__title,
			demoscene_production.supertype AS production__supertype,
			demoscene_production.unparsed_byline AS production__unparsed_byline,
			author_nick.id AS production__author_nicks__id,
			author_nick.name AS production__author_nicks__name,
			author.id AS production__author_nicks__releaser__id,
			author.is_group AS production__author_nicks__releaser__is_group,
			affiliation_nick.id AS production__author_affiliation_nicks__id,
			affiliation_nick.name AS production__author_affiliation_nicks__name,
			affiliation.id AS production__author_affiliation_nicks__releaser__id,
			affiliation.is_group AS production__author_affiliation_nicks__releaser__is_group
		FROM demoscene_competitionplacing
		LEFT JOIN demoscene_production ON (demoscene_competitionplacing.production_id = demoscene_production.id)
		LEFT JOIN demoscene_production_author_nicks ON (demoscene_production_author_nicks.production_id = demoscene_production.id)
		LEFT JOIN demoscene_nick AS author_nick ON (demoscene_production_author_nicks.nick_id = author_nick.id)
		LEFT JOIN demoscene_releaser AS author ON (author_nick.releaser_id = author.id)
		LEFT JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production_author_affiliation_nicks.production_id = demoscene_production.id)
		LEFT JOIN demoscene_nick AS affiliation_nick ON (demoscene_production_author_affiliation_nicks.nick_id = affiliation_nick.id)
		LEFT JOIN demoscene_releaser AS affiliation ON (affiliation_nick.releaser_id = affiliation.id)
		WHERE demoscene_competitionplacing.competition_id = %s
		ORDER BY
			demoscene_competitionplacing.position,
			demoscene_production.id, author_nick.id, affiliation_nick.id
	'''
	placings = unjoinify(CompetitionPlacing, query, (competition.id,), columns)

	return render(request, 'competitions/show.html', {
		'competition': competition,
		'placings': placings,
	})


def history(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)
	return render(request, 'competitions/history.html', {
		'competition': competition,
		'edits': Edit.for_model(competition),
	})
