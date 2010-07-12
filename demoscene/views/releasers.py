from demoscene.shortcuts import *
from demoscene.models import Releaser, NickVariant, Production, Nick, Credit
from demoscene.forms import ReleaserAddCreditForm
from django.contrib.auth.decorators import login_required

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

@login_required
def add_credit(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if request.method == 'POST':
		form = ReleaserAddCreditForm(releaser, request.POST)
		if form.is_valid():
			production = Production.objects.get(id = form.cleaned_data['production_id'])
			credit = Credit(
				production = production,
				nick = form.cleaned_data['nick_id'],
				role = form.cleaned_data['role']
			)
			credit.save()
			return HttpResponseRedirect(releaser.get_absolute_url())
	else:
		form = ReleaserAddCreditForm(releaser)
	return render(request, 'releasers/add_credit.html', {
		'releaser': releaser,
		'form': form,
	})
