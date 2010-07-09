from demoscene.shortcuts import *
from demoscene.models import NickVariant

def autocomplete(request):
	query = request.GET.get('q')
	new_option = request.GET.get('new_option', False)
	nick_variants = NickVariant.autocompletion_search(query,
		limit = request.GET.get('limit', 10),
		exact = request.GET.get('exact', False),
		groups = request.GET.getlist('group[]')
	)
	return render(request, 'releasers/autocomplete.txt', {
		'query': query,
		'nick_variants': nick_variants,
		'new_option': new_option,
	}, mimetype = 'text/plain')
