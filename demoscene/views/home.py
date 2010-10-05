from demoscene.shortcuts import *
from demoscene.models import Releaser, Production

def home(request):
	return render(request, 'home.html', {
		'latest_added_productions': Production.objects.order_by('-created_at')[0:10],
		'latest_updated_productions': Production.objects.order_by('-updated_at')[0:10],
		'latest_added_groups': Releaser.objects.filter(is_group = True).order_by('-created_at')[0:10],
		'latest_updated_groups': Releaser.objects.filter(is_group = True).order_by('-updated_at')[0:10],
		'latest_added_sceners': Releaser.objects.filter(is_group = False).order_by('-created_at')[0:10],
		'latest_updated_sceners': Releaser.objects.filter(is_group = False).order_by('-updated_at')[0:10],
	})
