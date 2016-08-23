from django import forms
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from demoscene.models import SceneID
from read_only_mode import writeable_site_required

import base64
import urllib
import urllib2
import json
import re


class SceneIDUserSignupForm(UserCreationForm):
	def __init__(self, *args, **kwargs):
		super(SceneIDUserSignupForm, self).__init__(*args, **kwargs)
		del self.fields['password1']
		del self.fields['password2']

	def clean_password2(self):
		return ""

	email = forms.EmailField(required=False, help_text=_('Needed if you want to be able to reset your password later on'))

	class Meta:
		fields = ('username', 'email')
		model = User


def do_sceneid_request(url, params, headers, method="GET"):
	data = urllib.urlencode(params)
	if (method == "GET"):
		request = urllib2.Request(settings.SCENEID_HOST + url + "?" + data, None, headers)
	else:
		request = urllib2.Request(settings.SCENEID_HOST + url, data, headers)

	response = urllib2.urlopen(request)
	response_json = response.read()

	response_data = json.loads(response_json)

	return response_data


@writeable_site_required
def do_auth_redirect(request):
	"""
	Generate the SceneID auth redirect URL and send user there.
	"""
	response = redirect(settings.SCENEID_HOST + 'oauth/authorize/')

	request.session['sceneid_state'] = get_random_string(length=32)

	params = {
		'client_id': settings.SCENEID_KEY,
		'redirect_uri': settings.BASE_URL + reverse('sceneid_return'),
		'response_type': 'code',
		'state': request.session['sceneid_state']
	}

	response['Location'] += '?' + urllib.urlencode(params)

	return response


@writeable_site_required
def process_response(request):
	"""
	Process the SceneID Oauth response
	"""
	state = request.GET.get('state', None)
	if (state is None):
		return HttpResponse("state missing!")  # todo proper exception

	code = request.GET.get('code', None)
	if (code is None):
		return HttpResponse("code missing!")  # todo proper exception

	if (state != request.session['sceneid_state']):
		return HttpResponse("state mismatch!")  # todo proper exception

	# request 1: turn response code into access token via endpoint

	auth_string = "Basic " + base64.b64encode(settings.SCENEID_KEY + ":" + settings.SCENEID_SECRET)

	params = {
		'grant_type': 'authorization_code',
		'code': code,
		'redirect_uri': settings.BASE_URL + reverse('sceneid_return'),
	}

	headers = {
		'Authorization': auth_string,
	}

	response_data = do_sceneid_request('oauth/token/', params, headers, "POST")

	# -- we can save these for later if we want to
	#request.session['sceneid_accesstoken'] = response_data["access_token"]
	#request.session['sceneid_refreshtoken'] = response_data["refresh_token"]

	# request 2: get current user
	headers = {
		'Authorization': "Bearer " + response_data["access_token"]
	}

	response_data = do_sceneid_request('api/3.0/me/', {}, headers, "GET")

	# authenticate user via django using our own backend
	user = authenticate(sceneid=response_data["user"]["id"])
	if user is not None:
		login(request, user)
	else:
		request.session['sceneid_login_userdata'] = response_data["user"]
		return redirect(reverse('sceneid_connect'))

	return redirect('home')


@writeable_site_required
def connect_accounts(request):
	if request.session['sceneid_login_userdata'] is None:
		return None

	form = SceneIDUserSignupForm(initial={
		'username': re.sub(r"[^a-z0-9A-Z]+", "", request.session['sceneid_login_userdata']['display_name'])
	})
	if request.POST.get("accountExisting"):
		user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
		if user is not None:
			sceneid = SceneID(user=user, sceneid=request.session['sceneid_login_userdata']['id'])
			sceneid.save()
			login(request, user)
			del request.session['sceneid_login_userdata']
			return redirect('home')
		else:
			messages.error(request, "Invalid login!")
	elif request.POST.get("accountNew"):
		form = SceneIDUserSignupForm(request.POST)
		if form.is_valid():
			form.cleaned_data["password1"] = get_random_string(length=32)
			form.save()
			user = authenticate(username=request.POST.get("username"), password=form.cleaned_data["password1"])
			sceneid = SceneID(user=user, sceneid=request.session['sceneid_login_userdata']['id'])
			sceneid.save()
			login(request, user)
			del request.session['sceneid_login_userdata']
			return redirect('home')

	return render(request, 'shared/sceneid_connect_accounts.html', {
		'nick': request.session['sceneid_login_userdata']['display_name'],
		'form': form,
	})
