from demoscene.models import AccountProfile
from users.utils import get_client_ip


class IPMiddleware:
    """
    Middleware that saves the user's IP address to their profile on each request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            AccountProfile.objects.update_or_create(user=request.user, defaults={"last_ip": get_client_ip(request)})
        return self.get_response(request)
