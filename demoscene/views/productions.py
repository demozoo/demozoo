from demoscene.shortcuts import *
from demoscene.models import Production

def index(request):
	productions = Production.objects.order_by('title')
	return render(request, 'productions/index.html', {
		'productions': productions,
	})
