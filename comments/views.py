from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from bbs.models import BBS
from comments.forms import CommentForm
from comments.models import Comment
from common.views import AjaxConfirmationView, writeable_site_required
from parties.models import Party
from productions.models import Production


class AddCommentView(TemplateView):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        commentable_id = self.args[0]
        self.commentable = get_object_or_404(self.commentable_model, id=commentable_id)
        self.comment = Comment(commentable=self.commentable, user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = CommentForm(instance=self.comment, prefix="comment")
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.form = CommentForm(request.POST, instance=self.comment, prefix="comment")
        if self.form.is_valid():
            self.form.save()
            return redirect(self.commentable.get_absolute_url() + ("#comment-%d" % self.comment.id))
        else:
            context = self.get_context_data()
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["commentable"] = self.commentable
        context["commentable_name"] = str(self.commentable)
        context["comment_form"] = self.form
        context["submit_action"] = self.submit_action
        return context

    template_name = "comments/add_comment.html"


class AddProductionCommentView(AddCommentView):
    commentable_model = Production
    submit_action = "add_production_comment"


class AddPartyCommentView(AddCommentView):
    commentable_model = Party
    submit_action = "add_party_comment"


class AddBBSCommentView(AddCommentView):
    commentable_model = BBS
    submit_action = "add_bbs_comment"


class EditCommentView(TemplateView):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        commentable_id = self.args[0]
        comment_id = self.args[1]

        commentable_type = ContentType.objects.get_for_model(self.commentable_model)
        self.commentable = get_object_or_404(self.commentable_model, id=commentable_id)
        self.comment = get_object_or_404(
            Comment, id=comment_id, content_type=commentable_type, object_id=commentable_id
        )

        if not request.user.is_staff:
            return redirect(self.comment.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = CommentForm(instance=self.comment, prefix="comment")
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.form = CommentForm(request.POST, instance=self.comment, prefix="comment")
        if self.form.is_valid():
            self.form.save()
            return redirect(self.comment.get_absolute_url())
        else:
            context = self.get_context_data()
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["commentable"] = self.commentable
        context["commentable_name"] = str(self.commentable)
        context["comment"] = self.comment
        context["comment_form"] = self.form
        context["submit_action"] = self.submit_action
        return context

    template_name = "comments/edit_comment.html"


class EditProductionCommentView(EditCommentView):
    commentable_model = Production
    submit_action = "edit_production_comment"


class EditPartyCommentView(EditCommentView):
    commentable_model = Party
    submit_action = "edit_party_comment"


class EditBBSCommentView(EditCommentView):
    commentable_model = BBS
    submit_action = "edit_bbs_comment"


class DeleteCommentView(AjaxConfirmationView):
    def get_object(self, request, commentable_id, comment_id):
        commentable_type = ContentType.objects.get_for_model(self.commentable_model)
        self.commentable = self.commentable_model.objects.get(id=commentable_id)
        self.comment = Comment.objects.get(id=comment_id, content_type=commentable_type, object_id=commentable_id)

    def get_cancel_url(self):
        return self.comment.get_absolute_url()

    def get_redirect_url(self):
        return self.commentable.get_absolute_url()

    def get_action_url(self):
        return reverse(self.action_url_path, args=[self.commentable.id, self.comment.id])

    def is_permitted(self):
        return self.request.user.is_staff

    def get_message(self):
        return "Are you sure you want to delete this comment?"

    def get_html_title(self):
        return "Deleting comment on %s" % str(self.commentable)

    def perform_action(self):
        self.comment.delete()


class DeleteProductionCommentView(DeleteCommentView):
    commentable_model = Production
    action_url_path = "delete_production_comment"


class DeletePartyCommentView(DeleteCommentView):
    commentable_model = Party
    action_url_path = "delete_party_comment"


class DeleteBBSCommentView(DeleteCommentView):
    commentable_model = BBS
    action_url_path = "delete_bbs_comment"
