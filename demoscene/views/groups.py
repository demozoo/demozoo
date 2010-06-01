from demoscene.shortcuts import *
from demoscene.models import Releaser

def index(request):
	groups = Releaser.objects.filter(is_group = True).order_by('name')
	return render(request, 'groups/index.html', {
		'groups': groups,
	})

def show(request, group_id):
	pass

def edit(request, production_id):
	pass

def create(request):
	pass