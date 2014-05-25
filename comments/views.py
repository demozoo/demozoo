from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from read_only_mode import writeable_site_required

from comments.models import Comment
from comments.forms import ProductionCommentForm
from demoscene.models import Production
from demoscene.shortcuts import simple_ajax_confirmation

@writeable_site_required
@login_required
def add_production_comment(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	comment = Comment(commentable=production, user=request.user)

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

@writeable_site_required
@login_required
def edit_production_comment(request, production_id, comment_id):
	production_type = ContentType.objects.get_for_model(Production)

	production = get_object_or_404(Production, id=production_id)
	comment = get_object_or_404(Comment,
		id=comment_id, content_type=production_type, object_id=production_id)

	if not request.user.is_staff:
		return redirect(production.get_absolute_url() + ('#comment-%d' % comment.id))

	if request.POST:
		form = ProductionCommentForm(request.POST, instance=comment, prefix='comment')
		if form.is_valid():
			form.save()
			return redirect(production.get_absolute_url() + ('#comment-%d' % comment.id))
	else:
		form = ProductionCommentForm(instance=comment, prefix='comment')

	return render(request, 'comments/edit_production_comment.html', {
		'production': production,
		'comment': comment,
		'comment_form': form,
	})

@writeable_site_required
@login_required
def delete_production_comment(request, production_id, comment_id):
	production_type = ContentType.objects.get_for_model(Production)

	production = get_object_or_404(Production, id=production_id)
	comment = get_object_or_404(Comment,
		id=comment_id, content_type=production_type, object_id=production_id)

	if not request.user.is_staff:
		return redirect(production.get_absolute_url() + ('#comment-%d' % comment.id))

	if request.method == 'POST':
		if request.POST.get('yes'):
			comment.delete()
		return redirect(production.get_absolute_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('delete_production_comment', args=[production_id, comment_id]),
			"Are you sure you want to delete this comment?",
			html_title="Deleting comment on %s" % production.title)
