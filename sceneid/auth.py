from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.utils.crypto import get_random_string
from django.http import HttpResponse

import base64
import urllib
import urllib2
import json

def do_sceneid_request(url,params,headers,method="GET"):
	data = urllib.urlencode(params)
	if (method == "GET"):
		request = urllib2.Request(settings.SCENEID_HOST + url + "?" + data)
	else:
		request = urllib2.Request(settings.SCENEID_HOST + url, data)

	for key in headers:
		request.add_header(key,headers[key])
		
	response = urllib2.urlopen(request)
	response_json = response.read()
	
	response_data = json.loads(response_json)

	return response_data
	
def do_auth_redirect(request):
	"""
	Generate the SceneID auth redirect URL and send user there.
	"""
	response = redirect(settings.SCENEID_HOST + 'oauth/authorize/')
	
	request.session['sceneid_state'] = get_random_string(length=32)
	 
	params = {}
	params["client_id"] = settings.SCENEID_KEY
	params["redirect_uri"] = settings.BASE_URL + reverse('sceneid_return')
	params["response_type"] = "code"
	params["state"] = request.session['sceneid_state']

	response['Location'] += '?' + urllib.urlencode(params)
	
	return response

def process_response(request):
	"""
	Process the SceneID Oauth response
	"""
	state = request.GET.get('state', None)
	if (state is None):
		return HttpResponse("state missing!") # todo proper exception

	code = request.GET.get('code', None)
	if (code is None):
		return HttpResponse("code missing!") # todo proper exception

	if (state != request.session['sceneid_state']):
		return HttpResponse("state mismatch!") # todo proper exception
	
	# request 1: turn response code into access token via endpoint
	
	auth_string = "Basic " + base64.b64encode( settings.SCENEID_KEY + ":" + settings.SCENEID_SECRET );

	params = {}
	params["grant_type"] = "authorization_code"
	params["code"] = code
	params["redirect_uri"] = settings.BASE_URL + reverse('sceneid_return')

	headers = {}
	headers["Authorization"] = auth_string
	
	response_data = do_sceneid_request( 'oauth/token/', params, headers, "POST" )

	# -- we can save these for later if we want to
	#request.session['sceneid_accesstoken'] = response_data["access_token"]
	#request.session['sceneid_refreshtoken'] = response_data["refresh_token"]

	# request 2: get current user
	headers = {}
	headers["Authorization"] = "Bearer " + response_data["access_token"]

	response_data = do_sceneid_request( 'api/3.0/me/', {}, headers, "GET" )
	
	# authenticate user via django using our own backend
	user = authenticate(sceneid=response_data["user"]["id"])
	if user is not None:
		login(request,user)
	else:
		pass # -- this is where we prompt the user to some sort of register-or-login form
	
	return redirect('home')