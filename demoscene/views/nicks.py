from nick_field import NickLookup
from byline_field import BylineLookup
from demoscene.models import NickVariant
from django.http import HttpResponse
try:
	import json
except ImportError:
	import simplejson as json

def match(request):
	initial_query = request.GET.get('q').lstrip() # only lstrip, because whitespace on right may be significant for autocompletion
	field_name = request.GET.get('field_name')
	autocomplete = request.GET.get('autocomplete', False)
	sceners_only = request.GET.get('sceners_only', False)
	groups_only = request.GET.get('groups_only', False)
	
	# irritating workaround for not being able to pass an "omit this parameter" value to jquery
	if autocomplete == 'false' or autocomplete == 'null' or autocomplete == '0':
		autocomplete = False
	
	filters = {} # also doubles up as options to pass to MatchedNickField
	if sceners_only:
		filters['sceners_only'] = True
	elif groups_only:
		filters['groups_only'] = True
	
	if autocomplete:
		query = initial_query + NickVariant.autocomplete(initial_query, **filters)
	else:
		query = initial_query
	
	nick_lookup = NickLookup(search_term = query.rstrip(), matched_nick_options = filters)
	
	data = {
		'query': query,
		'initial_query': initial_query,
		'matches': nick_lookup.matched_nick_field.widget.render(field_name, None),
	}
	# to simulate network lag:
	#import time
	#time.sleep(2)
	return HttpResponse(json.dumps(data), mimetype="text/javascript")

def byline_match(request):
	initial_query = request.GET.get('q')
	field_name = request.GET.get('field_name')
	autocomplete = request.GET.get('autocomplete', False)
	
	# irritating workaround for not being able to pass an "omit this parameter" value to jquery
	if autocomplete == 'false' or autocomplete == 'null' or autocomplete == '0':
		autocomplete = False
	
	byline_lookup = BylineLookup(search_term = initial_query, autocomplete = autocomplete)
	
	data = {
		'query': byline_lookup.search_term,
		'initial_query': initial_query,
		'matches': byline_lookup.render_match_fields(field_name),
	}
	return HttpResponse(json.dumps(data), mimetype="text/javascript")
	
	# alternative (non-functional) response to get django debug toolbar to show up
	#return HttpResponse("<body>%s</body>" % json.dumps(data))
