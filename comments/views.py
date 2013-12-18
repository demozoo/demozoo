from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from comments.models import ProductionComment
from comments.forms import ProductionCommentForm
from demoscene.models import Production

@login_required
def add_production_comment(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	comment = ProductionComment(production=production, user=request.user)

	if request.POST:
		form = ProductionCommentForm(request.POST, instance=comment, prefix='comment')
		if form.is_valid():
			form.save()
			return redirect(production.get_absolute_url() + ('#comment-%d' % comment.id))
	else:
		form = ProductionCommentForm(instance=comment, prefix='comment')

	return render(request, 'comments/add_production_comment.html', {
		'production': production,
		'comment_form': form,
	})
