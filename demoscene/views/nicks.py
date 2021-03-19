from __future__ import absolute_import, unicode_literals

import json

from django.http import HttpResponse

from demoscene.models import NickVariant
from demoscene.utils.nick_search import BylineSearch, NickSearch


def match(request):
    initial_query = request.GET.get('q')
    autocomplete = request.GET.get('autocomplete', False)
    sceners_only = request.GET.get('sceners_only', False)
    groups_only = request.GET.get('groups_only', False)
    group_ids = request.GET.get('group_ids')

    # irritating workaround for not being able to pass an "omit this parameter" value to jquery
    if autocomplete == 'false' or autocomplete == 'null' or autocomplete == '0':
        autocomplete = False

    filters = {}  # also doubles up as options to pass to NickSearch

    if group_ids:
        filters['group_ids'] = group_ids.split(',')
    if sceners_only:
        filters['sceners_only'] = True
    elif groups_only:
        filters['groups_only'] = True

    if autocomplete:
        query = initial_query + NickVariant.autocomplete(initial_query, **filters)
    else:
        query = initial_query

    nick_search = NickSearch(query.strip(), **filters)

    data = {
        'query': query,
        'initial_query': initial_query,
        'match': nick_search.match_data,
    }
    # to simulate network lag:
    #import time
    #time.sleep(2)
    return HttpResponse(json.dumps(data), content_type="text/javascript")


def byline_match(request):
    initial_query = request.GET.get('q')
    autocomplete = request.GET.get('autocomplete', False)

    # irritating workaround for not being able to pass an "omit this parameter" value to jquery
    if autocomplete == 'false' or autocomplete == 'null' or autocomplete == '0':
        autocomplete = False

    byline_search = BylineSearch(search_term=initial_query, autocomplete=autocomplete)

    data = {
        'query': byline_search.search_term,
        'initial_query': initial_query,
        'author_matches': byline_search.author_matches_data,
        'affiliation_matches': byline_search.affiliation_matches_data,
    }
    return HttpResponse(json.dumps(data), content_type="text/javascript")

    # alternative (non-functional) response to get django debug toolbar to show up
    #return HttpResponse("<body>%s</body>" % json.dumps(data))
