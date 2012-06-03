from demoscene.shortcuts import *
from demoscene.models import Releaser, Production, Edit


def home(request):
	return render(request, 'home.html', {
		'latest_added_productions': Production.objects.order_by('-created_at')[0:10],
		'latest_updated_productions': Production.objects.order_by('-updated_at')[0:10],
		'latest_added_groups': Releaser.objects.filter(is_group=True).order_by('-created_at')[0:10],
		'latest_updated_groups': Releaser.objects.filter(is_group=True).order_by('-updated_at')[0:10],
		'latest_added_sceners': Releaser.objects.filter(is_group=False).order_by('-created_at')[0:10],
		'latest_updated_sceners': Releaser.objects.filter(is_group=False).order_by('-updated_at')[0:10],
		'stats': {
			'production_count': Production.objects.filter(supertype='production').count(),
			'graphics_count': Production.objects.filter(supertype='graphics').count(),
			'music_count': Production.objects.filter(supertype='music').count(),
			'scener_count': Releaser.objects.filter(is_group=False).count(),
			'group_count': Releaser.objects.filter(is_group=True).count(),
		}
	})


def recent_edits(request):
	edits = Edit.objects.order_by('-timestamp').select_related('user', 'focus')
	edits_page = get_page(
		edits,
		request.GET.get('page', '1'))

	return render(request, 'recent_edits.html', {
		'edits_page': edits_page,
	})
