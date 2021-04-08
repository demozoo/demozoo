from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from read_only_mode import writeable_site_required

from demoscene.models import Edit


class AjaxConfirmationView(View):
    html_title = "%s"
    message = "%s"

    def get_redirect_url(self):
        return self.object.get_absolute_url()

    def redirect(self):
        return HttpResponseRedirect(self.get_redirect_url())

    def get_cancel_url(self):
        return self.get_redirect_url()

    def cancel(self):
        return HttpResponseRedirect(self.get_cancel_url())

    def get_permission_denied_url(self):
        return self.get_cancel_url()

    def permission_denied(self):
        return HttpResponseRedirect(self.get_permission_denied_url())

    def is_permitted(self):  # pragma: no cover
        return True

    def get_object(self, request, *args, **kwargs):  # pragma: no cover
        return None

    def perform_action(self):  # pragma: no cover
        pass

    def get_action_url(self):
        return reverse(self.action_url_path, args=[self.object.id])

    def get_message(self):
        return self.message % str(self.object)

    def get_html_title(self):
        return self.html_title % str(self.object)

    def validate(self):
        if not self.is_permitted():
            return self.permission_denied()

    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.object = self.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404("No object matches the given query.")

        response = self.validate()
        if response:
            return response

        if request.method == 'POST':
            if request.POST.get('yes'):
                self.perform_action()
                return self.redirect()
            else:
                return self.cancel()
        else:
            return render(request, 'shared/simple_confirmation.html', {
                'html_title': self.get_html_title(),
                'message': self.get_message(),
                'action_url': self.get_action_url(),
            })


class EditTextFilesView(View):
    def can_edit(self, subject):  # pragma: no cover
        return True

    def mark_as_edited(self, subject):  # pragma: no cover
        pass

    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, subject_id):
        self.subject = get_object_or_404(self.subject_model, id=subject_id)
        if not self.can_edit(self.subject):
            raise PermissionDenied

        self.relation = getattr(self.subject, self.relation_name)
        text_file_model = self.subject_model._meta.get_field(self.relation_name).related_model

        if request.method == 'POST':
            action_descriptions = []
            all_valid = True

            if request.user.is_staff:  # only staff members can edit/delete existing text files
                formset = self.formset_class(request.POST, instance=self.subject)
                all_valid = formset.is_valid()
                if all_valid:
                    formset.save()
                    if formset.deleted_objects:
                        deleted_files = [text_file.filename for text_file in formset.deleted_objects]
                        filename_list = ", ".join(deleted_files)
                        if len(deleted_files) > 1:
                            action_descriptions.append(
                                u"Deleted %s: %s" % (text_file_model._meta.verbose_name_plural, filename_list)
                            )
                        else:
                            action_descriptions.append(
                                u"Deleted %s %s" % (text_file_model._meta.verbose_name, filename_list)
                            )

            if all_valid:
                uploaded_files = request.FILES.getlist(self.upload_field_name)
                file_count = len(uploaded_files)
                for f in uploaded_files:
                    self.relation.create(file=f)

                if file_count:
                    if file_count == 1:
                        action_descriptions.append("Added %s" % text_file_model._meta.verbose_name)
                    else:
                        action_descriptions.append(
                            "Added %s %s" % (file_count, text_file_model._meta.verbose_name_plural)
                        )

                if action_descriptions:
                    # at least one change was made
                    action_description = '; '.join(action_descriptions)
                    self.mark_as_edited(self.subject)

                    Edit.objects.create(
                        action_type='edit_info_files', focus=self.subject,
                        description=action_description, user=request.user
                    )

                return HttpResponseRedirect(self.subject.get_absolute_url())

        else:
            formset = self.formset_class(instance=self.subject)

        return render(request, self.template_name, {
            self.subject_context_name: self.subject,
            'formset': formset,
            'add_only': (not request.user.is_staff) or (self.relation.count() == 0),
        })
