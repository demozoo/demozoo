from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView

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
