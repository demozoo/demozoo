from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import BaseHasAPIKey

from users.models import APIKey


class HasAPIKey(BaseHasAPIKey):
    model = APIKey


IsAuthenticatedOrHasAPIKey = IsAuthenticated | HasAPIKey
