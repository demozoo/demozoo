from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import BaseHasAPIKey, KeyParser

from users.models import APIKey


class URLKeyParser(KeyParser):
    def get(self, request):
        # allow passing the API key in the query string as well as in the Authorization header, for convenience
        return super().get(request) or request.GET.get("api_key")


class HasAPIKey(BaseHasAPIKey):
    model = APIKey
    key_parser = URLKeyParser()


IsAuthenticatedOrHasAPIKey = IsAuthenticated | HasAPIKey
