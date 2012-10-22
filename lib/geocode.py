from django.conf import settings
import urllib, urllib2  # yay, let's arbitrarily split useful functions across two meaninglessly-named libraries!
from django.utils import simplejson as json
import re

strip_nonalpha = re.compile(r'[^\w\-\ \,\.]', re.UNICODE)


def geocode(location):
	# strip out punctuation other than a minimal whitelisted set, because Yahoo doesn't give us
	# an escaping mechanism for single quotes (or has crap documentation that doesn't tell us about it)
	location = re.sub(strip_nonalpha, '', location).encode('utf-8')
	params = {
		'format': 'json',
		'appid': settings.YAHOO_API_KEY
	}
	url = "http://where.yahooapis.com/v1/places.q('%s')?%s" % (urllib.quote(location), urllib.urlencode(params))
	f = urllib2.urlopen(url)
	response = json.load(f)
	f.close()

	if response['places']['count']:
		result = response['places']['place'][0]

		if result['placeTypeName attrs']['code'] == 12 or not result['country']:
			# place is a country or international entity (continent, sea...) - just use the name
			location = result['name']
		elif result['placeTypeName attrs']['code'] in (10, 20, 22) and result['locality1'] and result['locality1'] != result['name']:
			# place is a tertiary region or suburb or point of interest, with something meaningful in 'locality1' (hopefully a town name)
			location = "%s, %s, %s" % (result['name'], result['locality1'], result['country'])
		else:
			# use name + country
			location = "%s, %s" % (result['name'], result['country'])

		try:
			latitude = result['centroid']['latitude']
			longitude = result['centroid']['longitude']
		except KeyError:
			latitude = None
			longitude = None

		try:
			country_code = result['country attrs']['code']
		except KeyError:
			country_code = None

		return {
			'location': location,
			'woeid': result['woeid'],
			'latitude': latitude,
			'longitude': longitude,
			'country_code': country_code,
		}
	else:
		return None
