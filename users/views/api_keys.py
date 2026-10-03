from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from common.views import AjaxConfirmationView, EditingFormView, writeable_site_required
from users.forms import APIKeyForm
from users.models import APIKey


@method_decorator(login_required, name="dispatch")
class APIKeyListView(ListView):
    model = APIKey
    template_name = "users/api_keys.html"
    context_object_name = "api_keys"

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_keys_enforced"] = settings.ENFORCE_API_KEYS
        return context


@method_decorator(login_required, name="dispatch")
@method_decorator(writeable_site_required, name="dispatch")
class APIKeyCreateView(EditingFormView):
    form_class = APIKeyForm
    title = "Create new API key"
    submit_button_label = "Create"
    action_url_name = "api_keys_create"

    def form_valid(self):
        self.object, self.key = APIKey.objects.create_key(name=self.form.cleaned_data["name"], user=self.request.user)

    def render_success_response(self):
        messages.success(
            self.request,
            f"API key created successfully. Please copy the key now, as it will not be shown again: {self.key}",
        )
        return redirect(reverse("api_keys_index"))


class RevokeAPIKeyView(AjaxConfirmationView):
    html_title = "Revoking API key: %s"
    message = "Are you sure you want to revoke the API key '%s'?"
    action_url_path = "revoke_api_key"

    def get_object(self, request, api_key_id):
        return request.user.api_keys.get(id=api_key_id)

    def get_redirect_url(self):
        return reverse("api_keys_index")

    def get_cancel_url(self):
        return reverse("api_keys_index")

    def perform_action(self):
        self.object.revoked = True
        self.object.save(update_fields=["revoked"])
        messages.success(self.request, "API key '%s' revoked" % self.object.name)
