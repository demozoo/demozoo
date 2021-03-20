from __future__ import absolute_import, unicode_literals

import base64
import json
import re
import urllib

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from read_only_mode import writeable_site_required

from demoscene.models import SceneID


class SceneIDUserSignupForm(forms.ModelForm):
    email = forms.EmailField(
        required=False, help_text=_('Needed if you want to be able to reset your password later on')
    )

    def save(self, commit=True):
        user = super(SceneIDUserSignupForm, self).save(commit=False)
        user.set_unusable_password()
        if commit:
            user.save()
        return user

    class Meta:
        fields = ('username', 'email')
        model = User


def do_sceneid_request(url, params, headers, method="GET"):
    data = urllib.parse.urlencode(params)
    if (method == "GET"):
        request = urllib.request.Request(settings.SCENEID_HOST + url + "?" + data, None, headers)
    else:
        request = urllib.request.Request(settings.SCENEID_HOST + url, data.encode('ascii'), headers)

    response = urllib.request.urlopen(request)
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
    request.session['next'] = request.GET.get('next')

    params = {
        'client_id': settings.SCENEID_KEY,
        'redirect_uri': settings.BASE_URL + reverse('sceneid_return'),
        'response_type': 'code',
        'state': request.session['sceneid_state']
    }

    response['Location'] += '?' + urllib.parse.urlencode(params)

    return response


@writeable_site_required
def process_response(request):
    """
    Process the SceneID Oauth response
    """
    state = request.GET['state']
    code = request.GET['code']

    if (state != request.session['sceneid_state']):
        raise SuspiciousOperation("State mismatch!")

    # request 1: turn response code into access token via endpoint

    auth_string = "Basic " + base64.b64encode(
        settings.SCENEID_KEY.encode('ascii') + b':' + settings.SCENEID_SECRET.encode('ascii')
    ).decode('ascii')

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
    # request.session['sceneid_accesstoken'] = response_data["access_token"]
    # request.session['sceneid_refreshtoken'] = response_data["refresh_token"]

    # request 2: get current user
    headers = {
        'Authorization': "Bearer " + response_data["access_token"]
    }

    response_data = do_sceneid_request('api/3.0/me/', {}, headers, "GET")

    # authenticate user via django using our own backend
    user = authenticate(sceneid=response_data["user"]["id"])
    if user is not None:
        # we have a known active local user linked to this sceneid
        login(request, user)
    elif User.objects.filter(sceneid__sceneid=response_data["user"]["id"], is_active=False).exists():
        # user is recognised but deactivated
        messages.error(request, "Your account was disabled.")
    else:
        # no known user with this sceneid - prompt them to connect to a new or existing account
        request.session['sceneid_login_userdata'] = response_data["user"]
        return redirect(reverse('sceneid_connect'))

    return redirect(request.session.get('next') or 'home')


@writeable_site_required
def connect_accounts(request):
    if not request.session.get('sceneid_login_userdata'):
        return redirect('log_in')

    form = SceneIDUserSignupForm(initial={
        'username': re.sub(r"[^a-z0-9A-Z]+", "", request.session['sceneid_login_userdata']['display_name'])
    })
    if request.POST.get("accountExisting"):
        user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
        if user is not None and user.is_active:
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
            sceneid_num = request.session['sceneid_login_userdata']['id']
            user = form.save()
            SceneID.objects.create(user=user, sceneid=sceneid_num)
            user = authenticate(sceneid=sceneid_num)
            login(request, user)
            try:
                del request.session['sceneid_login_userdata']
            except KeyError:
                # login will overwrite request.session if the old session was authenticated
                pass
            return redirect('home')

    return render(request, 'shared/sceneid_connect_accounts.html', {
        'nick': request.session['sceneid_login_userdata']['display_name'],
        'form': form,
    })
