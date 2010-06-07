from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from demoscene.shortcuts import *
from django.contrib import messages

def signup(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			user = authenticate(
				username = form.cleaned_data['username'],
				password = form.cleaned_data['password1'],
			)
			login(request, user)
			messages.success(request, 'Account created')
			return redirect('home')
	else:
		form = UserCreationForm()
	return render(request, 'accounts/signup.html', {
		'form': form,
	})
