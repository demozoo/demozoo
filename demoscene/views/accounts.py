from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as base_login
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.shortcuts import render, redirect

from demoscene.forms.account import UserSignupForm
from demoscene.models import CaptchaQuestion
from demoscene.utils.accounts import is_ip_banned
from read_only_mode import writeable_site_required


def custom_login(request):
    if is_ip_banned(request):
        messages.error(request, "Your account was disabled.")
        return redirect('home')
    else:
        return base_login(request)


@writeable_site_required
@login_required
def index(request):
    return render(request, 'accounts/index.html', {})


@writeable_site_required
def signup(request):
    if is_ip_banned(request):
        messages.error(request, "Your account was disabled.")
        return redirect('home')

    if request.method == 'POST':
        captcha = CaptchaQuestion.objects.get(id=request.session.get('captcha_id'))

        form = UserSignupForm(request.POST, captcha=captcha)
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
            )
            login(request, user)
            messages.success(request, 'Account created')
            return redirect('home')
    else:
        captcha = CaptchaQuestion.objects.order_by('?')[0]
        request.session['captcha_id'] = captcha.id
        form = UserSignupForm(captcha=captcha)
    return render(request, 'accounts/signup.html', {
        'form': form,
    })


@writeable_site_required
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password updated')
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'shared/simple_form.html', {
        'form': form,
        'title': "Change password",
        'html_title': "Change password",
        'action_url': reverse('account_change_password'),
    })
