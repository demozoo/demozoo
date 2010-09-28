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
	
	# irritating workaround for not being able to pass an "omit this parameter" value to jquery
	if autocomplete == 'false' or autocomplete == 'null' or autocomplete == '0':
		autocomplete = False
	
	if autocomplete:
		if NickVariant.objects.filter(name__iexact = initial_query).count():
			# search term is already a complete recognised nick, so don't autocomplete further
			query = initial_query
		else:
			# look for possible autocompletions; choose the top-ranked one and use that as the query
			autocompletions = NickVariant.autocompletion_search(initial_query, limit = 1)
			try:
				query = autocompletions[0].name
				# substitute in the initial query as the prefix, so that capitalisation is preserved.
				# (iTunes fails to do this. Ha, I rule.)
				query = initial_query + query[len(initial_query):]
			except IndexError:
				query = initial_query
	else:
		query = initial_query
	
	mnf = MatchedNickField(query)
	
	data = {
		'query': query,
		'initial_query': initial_query,
		'matches': mnf.widget.render(field_name, None),
	}
	return HttpResponse(json.dumps(data), mimetype="text/javascript")
