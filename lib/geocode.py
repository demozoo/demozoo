from django.conf import settings
import urllib, urllib2 # yay, let's arbitrarily split useful functions across two meaninglessly-named libraries!
try:
	import json
except ImportError:
	import simplejson as json

def geocode(location):
	params = {
		'location': location.encode('utf-8'),
		'flags': 'J',
		'appid': settings.YAHOO_API_KEY
	}
	url = "http://where.yahooapis.com/geocode?%s" % urllib.urlencode(params)
	f = urllib2.urlopen(url)
	response = json.load(f)
	f.close()
	
	if response['ResultSet']['Found']:
		result = response['ResultSet']['Results'][0]
		# Return formats:
		# country|name (e.g. 'United Kingdom', 'Europe')
		# city|state, country|name (e.g. 'Helsinki, Finland'; 'Scotland, United Kingdom')
		# neighborhood, city|state, country|name (e.g. 'Charlbury, Chipping Norton, United Kingdom')
		location_parts = []
		if result['neighborhood']:
			location_parts.append(result['neighborhood'])
		city_or_state = result['city'] or result['state']
		if city_or_state:
			location_parts.append(city_or_state)
		location_parts.append(result['country'] or result['name'])
		return {
			'location': ', '.join(location_parts),
			'woeid': result['woeid'],
			'latitude': result['latitude'],
			'longitude': result['longitude'],
			'country_code': result['countrycode'],
		}
	else:
		return None
