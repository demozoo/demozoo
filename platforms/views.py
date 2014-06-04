from django.shortcuts import get_object_or_404, render
from platforms.models import Platform

def index(request):
	platforms = Platform.objects.order_by('name')
	return render(request, 'platforms/index.html', {
		'platforms': platforms,
	})

def show(request, platform_id):
	platform = get_object_or_404(Platform, id = platform_id)
	return render(request, 'platforms/show.html', {
		'platform': platform,
		'active_groups': platform.random_active_groups()[:],
		'productions': platform.productions.filter(release_date_date__isnull=False).select_related('default_screenshot').prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').order_by('-release_date_date', '-title')[0:30],
	})
