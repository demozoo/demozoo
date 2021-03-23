from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from read_only_mode import writeable_site_required


class AjaxConfirmationView(View):
    html_title = "%s"
    message = "%s"

    def get_redirect_url(self):
        return self.object.get_absolute_url()

    def redirect(self):
        return HttpResponseRedirect(self.get_redirect_url())

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

    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.object = self.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404("No object matches the given query.")

        if not self.is_permitted():
            return self.redirect()

        if request.method == 'POST':
            if request.POST.get('yes'):
                self.perform_action()
            return self.redirect()
        else:
            return render(request, 'shared/simple_confirmation.html', {
                'html_title': self.get_html_title(),
                'message': self.get_message(),
                'action_url': self.get_action_url(),
            })
