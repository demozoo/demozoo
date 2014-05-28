from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from read_only_mode import writeable_site_required

from comments.models import Comment
from comments.forms import CommentForm
from demoscene.models import Production
from demoscene.shortcuts import simple_ajax_confirmation


class AddProductionCommentView(TemplateView):
	@method_decorator(writeable_site_required)
	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		production_id = self.args[0]
		self.production = get_object_or_404(Production, id=production_id)
		self.comment = Comment(commentable=self.production, user=request.user)
		return super(AddProductionCommentView, self).dispatch(request, *args, **kwargs)

	def get(self, request, *args, **kwargs):
		self.form = CommentForm(instance=self.comment, prefix='comment')
		context = self.get_context_data()
		return self.render_to_response(context)

	def post(self, request, *args, **kwargs):
		self.form = CommentForm(request.POST, instance=self.comment, prefix='comment')
		if self.form.is_valid():
			self.form.save()
			return redirect(
				self.production.get_absolute_url() + ('#comment-%d' % self.comment.id)
			)
		else:
			context = self.get_context_data()
			return self.render_to_response(context)

	def get_context_data(self, **kwargs):
		context = super(AddProductionCommentView, self).get_context_data(**kwargs)
		context['production'] = self.production
		context['comment_form'] = self.form
		return context

	template_name = 'comments/add_production_comment.html'


class EditProductionCommentView(TemplateView):
	@method_decorator(writeable_site_required)
	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		production_id = self.args[0]
		comment_id = self.args[1]

		production_type = ContentType.objects.get_for_model(Production)
		self.production = get_object_or_404(Production, id=production_id)
		self.comment = get_object_or_404(Comment,
			id=comment_id, content_type=production_type, object_id=production_id)

		if not request.user.is_staff:
			return redirect(self.get_redirect_url())

		return super(EditProductionCommentView, self).dispatch(request, *args, **kwargs)

	def get(self, request, *args, **kwargs):
		self.form = CommentForm(instance=self.comment, prefix='comment')
		context = self.get_context_data()
		return self.render_to_response(context)

	def post(self, request, *args, **kwargs):
		self.form = CommentForm(request.POST, instance=self.comment, prefix='comment')
		if self.form.is_valid():
			self.form.save()
			return redirect(self.get_redirect_url())
		else:
			context = self.get_context_data()
			return self.render_to_response(context)

	def get_redirect_url(self):
		return self.production.get_absolute_url() + ('#comment-%d' % self.comment.id)

	def get_context_data(self, **kwargs):
		context = super(EditProductionCommentView, self).get_context_data(**kwargs)
		context['production'] = self.production
		context['comment'] = self.comment
		context['comment_form'] = self.form
		return context

	template_name = 'comments/edit_production_comment.html'


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
