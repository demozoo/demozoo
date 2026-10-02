from django.conf import settings
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey


class APIKey(AbstractAPIKey):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys")
