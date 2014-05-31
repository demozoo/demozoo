from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from read_only_mode import writeable_site_required

from comments.models import Comment
from comments.forms import CommentForm
from demoscene.models import Production
from demoscene.shortcuts import simple_ajax_confirmation
from parties.models import Party


class AddCommentView(TemplateView):
	@method_decorator(writeable_site_required)
	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		commentable_id = self.args[0]
		self.commentable = get_object_or_404(self.commentable_model, id=commentable_id)
		self.comment = Comment(commentable=self.commentable, user=request.user)
		return super(AddCommentView, self).dispatch(request, *args, **kwargs)

	def get(self, request, *args, **kwargs):
		self.form = CommentForm(instance=self.comment, prefix='comment')
		context = self.get_context_data()
		return self.render_to_response(context)

	def post(self, request, *args, **kwargs):
		self.form = CommentForm(request.POST, instance=self.comment, prefix='comment')
		if self.form.is_valid():
			self.form.save()
			return redirect(
				self.commentable.get_absolute_url() + ('#comment-%d' % self.comment.id)
			)
		else:
			context = self.get_context_data()
			return self.render_to_response(context)

	def get_context_data(self, **kwargs):
		context = super(AddCommentView, self).get_context_data(**kwargs)
		context['commentable'] = self.commentable
		context['commentable_name'] = self.get_commentable_name(self.commentable)
		context['comment_form'] = self.form
		context['submit_action'] = self.submit_action
		return context

	template_name = 'comments/add_comment.html'

class AddProductionCommentView(AddCommentView):
	commentable_model = Production
	submit_action = 'add_production_comment'

	def get_commentable_name(self, production):
		return production.title

class AddPartyCommentView(AddCommentView):
	commentable_model = Party
	submit_action = 'add_party_comment'

	def get_commentable_name(self, party):
		return party.name


class EditCommentView(TemplateView):
	@method_decorator(writeable_site_required)
	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		commentable_id = self.args[0]
		comment_id = self.args[1]

		commentable_type = ContentType.objects.get_for_model(self.commentable_model)
		self.commentable = get_object_or_404(self.commentable_model, id=commentable_id)
		self.comment = get_object_or_404(Comment,
			id=comment_id, content_type=commentable_type, object_id=commentable_id)

		if not request.user.is_staff:
			return redirect(self.comment.get_absolute_url())

		return super(EditCommentView, self).dispatch(request, *args, **kwargs)

	def get(self, request, *args, **kwargs):
		self.form = CommentForm(instance=self.comment, prefix='comment')
		context = self.get_context_data()
		return self.render_to_response(context)

	def post(self, request, *args, **kwargs):
		self.form = CommentForm(request.POST, instance=self.comment, prefix='comment')
		if self.form.is_valid():
			self.form.save()
			return redirect(self.comment.get_absolute_url())
		else:
			context = self.get_context_data()
			return self.render_to_response(context)

	def get_context_data(self, **kwargs):
		context = super(EditCommentView, self).get_context_data(**kwargs)
		context['commentable'] = self.commentable
		context['commentable_name'] = self.get_commentable_name(self.commentable)
		context['comment'] = self.comment
		context['comment_form'] = self.form
		context['submit_action'] = self.submit_action
		return context

	template_name = 'comments/edit_comment.html'

class EditProductionCommentView(EditCommentView):
	commentable_model = Production
	submit_action = 'edit_production_comment'

	def get_commentable_name(self, production):
		return production.title

class EditPartyCommentView(EditCommentView):
	commentable_model = Party
	submit_action = 'edit_party_comment'

	def get_commentable_name(self, party):
		return party.name


class DeleteCommentView(View):
	@method_decorator(writeable_site_required)
	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		commentable_id = self.args[0]
		comment_id = self.args[1]

		commentable_type = ContentType.objects.get_for_model(self.commentable_model)
		self.commentable = get_object_or_404(self.commentable_model, id=commentable_id)
		self.comment = get_object_or_404(Comment,
			id=comment_id, content_type=commentable_type, object_id=commentable_id)

		if not request.user.is_staff:
			return redirect(self.comment.get_absolute_url())

		return super(DeleteCommentView, self).dispatch(request, *args, **kwargs)

	def get(self, request, *args, **kwargs):
		commentable_name = self.get_commentable_name(self.commentable)
		return simple_ajax_confirmation(request,
			reverse(self.url_name, args=[self.commentable.id, self.comment.id]),
			"Are you sure you want to delete this comment?",
			html_title="Deleting comment on %s" % commentable_name)

	def post(self, request, *args, **kwargs):
		if request.POST.get('yes'):
			self.comment.delete()
			return redirect(self.commentable.get_absolute_url())
		else:
			return redirect(self.comment.get_absolute_url())

class DeleteProductionCommentView(DeleteCommentView):
	commentable_model = Production
	commentable_context_name = 'production'
	url_name = 'delete_production_comment'

	def get_commentable_name(self, production):
		return production.title

class DeletePartyCommentView(DeleteCommentView):
	commentable_model = Party
	commentable_context_name = 'party'
	url_name = 'delete_party_comment'

	def get_commentable_name(self, party):
		return party.name
