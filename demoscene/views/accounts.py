from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from demoscene.shortcuts import *
from demoscene.forms.account import *
from demoscene.models import AccountProfile


@login_required
def index(request):
	return render(request, 'accounts/index.html', {})


def signup(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
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
		form = UserCreationForm()
	return render(request, 'accounts/signup.html', {
		'form': form,
	})


@login_required
def preferences(request):
	try:
		profile = request.user.get_profile()
	except AccountProfile.DoesNotExist:
		profile = AccountProfile(user=request.user)
	if request.method == 'POST':
		form = AccountPreferencesForm(request.POST, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, 'Preferences updated')
			return redirect('home')
	else:
		form = AccountPreferencesForm(instance=profile)

	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Preferences",
		'html_title': "Preferences",
		'action_url': reverse('account_preferences'),
	})


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

	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Change password",
		'html_title': "Change password",
		'action_url': reverse('account_change_password'),
	})
