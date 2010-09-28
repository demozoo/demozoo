from nick_field import MatchedNickField
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
		if NickVariant.autocompletion_search(initial_query, exact = True, limit = 1, **filters).count():
			# search term is already a complete recognised nick, so don't autocomplete further
			query = initial_query
		else:
			# look for possible autocompletions; choose the top-ranked one and use that as the query
			autocompletions = NickVariant.autocompletion_search(initial_query, limit = 1, **filters)
			try:
				query = autocompletions[0].name
				# substitute in the initial query as the prefix, so that capitalisation is preserved.
				# (iTunes fails to do this. Ha, I rule.)
				query = initial_query + query[len(initial_query):]
			except IndexError:
				query = initial_query
	else:
		query = initial_query
	
	mnf = MatchedNickField(query, **filters)
	
	data = {
		'query': query,
		'initial_query': initial_query,
		'matches': mnf.widget.render(field_name, None),
	}
	return HttpResponse(json.dumps(data), mimetype="text/javascript")
