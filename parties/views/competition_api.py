from __future__ import absolute_import  # ensure that 'from parties.foo' imports find the top-level parties module, not parties.views.parties

import json
import datetime

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import F

from demoscene.models import Edit
from productions.models import Production, ProductionType
from parties.models import Competition, CompetitionPlacing
from platforms.models import Platform
from demoscene.utils.nick_search import NickSelection
from read_only_mode import writeable_site_required


# helper function: create or update a production according to JSON data
def handle_production(prod_data, competition):
    if prod_data.get('id'):
        production = Production.objects.get(id=prod_data['id'])
    else:
        production = Production(
            release_date=competition.shown_date,
            updated_at=datetime.datetime.now(),
            has_bonafide_edits=False)
        production.save()  # assign an ID so that associations work

    # can only edit production details if production is non-stable (which is always true for
    # newly-created ones)
    if not production.is_stable_for_competitions():
        if 'title' in prod_data:
            production.title = prod_data['title']
        if 'platform_id' in prod_data:
            if prod_data['platform_id']:
                production.platforms = [Platform.objects.get(id=prod_data['platform_id'])]
            else:
                production.platforms = []
        if 'production_type_id' in prod_data:
            if prod_data['production_type_id']:
                production.types = [ProductionType.objects.get(id=prod_data['production_type_id'])]
            else:
                production.types = []
        if 'byline' in prod_data:
            try:
                production.author_nicks = [
                    NickSelection(author['id'], author['name']).commit()
                    for author in prod_data['byline']['authors']
                ]
                production.author_affiliation_nicks = [
                    NickSelection(affillation['id'], affillation['name']).commit()
                    for affillation in prod_data['byline']['affiliations']
                ]
                production.unparsed_byline = None
            except NickSelection.FailedToResolve:
                # failed to match up the passed nick IDs to valid nick records.
                # Keep the passed names, as an unparsed byline
                author_names = [author['name'] for author in prod_data['byline']['authors']]
                affiliation_names = [affiliation['name'] for affiliation in prod_data['byline']['affiliations']]
                byline_string = ' + '.join(author_names)
                if affiliation_names:
                    byline_string += ' / ' + ' ^ '.join(affiliation_names)
                production.unparsed_byline = byline_string
                production.author_nicks = []
                production.author_affiliation_nicks = []

        production.updated_at = datetime.datetime.now()
        production.supertype = production.inferred_supertype
        production.save()

    return production


@writeable_site_required
@login_required
def add_placing(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)
    if request.method == 'POST':
        data = json.loads(request.body)

        # move existing placings to accommodate new entry at the stated position
        competition.placings.filter(position__gte=data['position']).update(position=F('position') + 1)

        production = handle_production(data['production'], competition)

        placing = CompetitionPlacing(
            production=production,
            competition=competition,
            ranking=data['ranking'],
            position=data['position'],
            score=data['score'],
        )
        placing.save()

        Edit.objects.create(action_type='add_competition_placing', focus=competition, focus2=production,
            description=(u"Added competition placing for %s in %s competition" % (production.title, competition)), user=request.user)

        return HttpResponse(json.dumps(placing.json_data), content_type="text/javascript")


@writeable_site_required
@login_required
def update_placing(request, placing_id):
    placing = get_object_or_404(CompetitionPlacing, id=placing_id)
    competition = placing.competition
    if request.method == 'POST':
        data = json.loads(request.body)

        # move existing placings to accommodate new entry at the stated position
        if int(data['position']) > placing.position:  # increasing position - move others down
            competition.placings.filter(position__gt=placing.position, position__lte=data['position']).update(position=F('position') - 1)
        elif int(data['position']) < placing.position:  # decreasing position - move others up
            competition.placings.filter(position__gte=data['position'], position__lt=placing.position).update(position=F('position') + 1)

        production = handle_production(data['production'], competition)

        Edit.objects.create(action_type='update_competition_placing', focus=competition, focus2=production,
            description=(u"Updated competition placing info for %s in %s competition" % (production.title, competition)), user=request.user)

        placing.production = production
        placing.ranking = data['ranking']
        placing.position = data['position']
        placing.score = data['score']
        placing.save()

        return HttpResponse(json.dumps(placing.json_data), content_type="text/javascript")


@writeable_site_required
@login_required
def delete_placing(request, placing_id):
    placing = get_object_or_404(CompetitionPlacing, id=placing_id)
    competition = placing.competition
    if request.method == 'POST':
        # Delete production entry too, if it wasn't stable; need to do this test before deleting
        # the placing, as number of placings is one criterion for whether it's stable or not
        delete_production_too = not placing.production.is_stable_for_competitions()
        placing.delete()
        # move remaining placings to close the gap
        competition.placings.filter(position__gt=placing.position).update(position=F('position') - 1)

        Edit.objects.create(action_type='remove_competition_placing', focus=competition, focus2=placing.production,
            description=(u"Removed competition placing for %s in %s competition" % (placing.production.title, competition)), user=request.user)

        if delete_production_too:
            placing.production.delete()

        return HttpResponse('OK', content_type="text/plain")
