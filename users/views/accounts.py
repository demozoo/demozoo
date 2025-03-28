from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from common.utils.ajax import request_is_ajax
from common.views import EditingFormView, writeable_site_required
from demoscene.forms.account import UserSignupForm
from demoscene.models import CaptchaQuestion
from users.utils import is_login_banned, is_registration_banned


class LoginViewWithIPCheck(LoginView):
    def dispatch(self, request, *args, **kwargs):
        if is_login_banned(request):
            messages.error(request, "Your account was disabled.")
            return redirect("home")
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_ajax"] = request_is_ajax(self.request)
        return context


@writeable_site_required
@login_required
def index(request):
    return render(request, "accounts/index.html", {})


@writeable_site_required
def signup(request):
    if is_login_banned(request):
        messages.error(request, "Your account was disabled.")
        return redirect("home")
    elif is_registration_banned(request):
        messages.error(
            request,
            "Due to a large number of sockpuppet accounts, new registrations from this location are blocked.",
        )
        return redirect("home")

    if request.method == "POST":
        captcha = CaptchaQuestion.objects.get(id=request.session.get("captcha_id"))

        form = UserSignupForm(request.POST, captcha=captcha)
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"],
            )
            login(request, user)
            messages.success(request, "Account created")
            return redirect("home")
    else:
        captcha = CaptchaQuestion.objects.order_by("?")[0]
        request.session["captcha_id"] = captcha.id
        form = UserSignupForm(captcha=captcha)
    return render(
        request,
        "accounts/signup.html",
        {
            "form": form,
        },
    )


class ChangePasswordView(EditingFormView):
    page_title = "Change password"
    action_url_name = "account_change_password"

    def get_form(self):
        if self.request.method == "POST":
            return PasswordChangeForm(self.request.user, self.request.POST)
        else:
            return PasswordChangeForm(self.request.user)

    def render_success_response(self):
        messages.success(self.request, "Password updated")
        return redirect("home")
