from datetime import timedelta

from demoscene.models import AccountProfile
from users.utils import get_client_ip


LOGIN_COOKIE = "is_an_atomic_playboy"


class IPMiddleware:
    """
    Middleware that saves the user's IP address to their profile on each request.
    Also sets an `is_an_atomic_playboy` cookie for logged-in users,
    so that we can bypass the Cloudflare captcha for them.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            AccountProfile.objects.update_or_create(user=request.user, defaults={"last_ip": get_client_ip(request)})
        response = self.get_response(request)
        if request.user.is_authenticated:
            response.set_cookie(
                LOGIN_COOKIE, "yes", max_age=timedelta(days=365), secure=True, httponly=True, samesite="None"
            )
        return response
