from demoscene.shortcuts import *
from demoscene.models import Platform

def index(request):
	platforms = Platform.objects.order_by('name')
	return render(request, 'platforms/index.html', {
		'platforms': platforms,
	})

def show(request, platform_id):
	platform = Platform.objects.get(id = platform_id)
	return render(request, 'platforms/show.html', {
		'platform': platform,
	})
