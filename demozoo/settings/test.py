from .base import *

import urllib2
from StringIO import StringIO


SECRET_KEY = 'BOOOOM'


# set up mock opener for urllib2

def mock_response(req):
	url = req.get_full_url()
	if url == 'http://geocoder.demozoo.org/?q=Oxford':
		body = """[
			{"name": "Oxford, Oxfordshire, England, United Kingdom", "id": 2640729},
			{"name": "Oxford, Butler County, Ohio, United States", "id": 4520760},
			{"name": "Oxford, Calhoun County, Alabama, United States", "id": 4081914}
		]"""
	elif url == 'http://geocoder.demozoo.org/2640729/':
		body = """{
			"full_name": "Oxford, Oxfordshire, England, United Kingdom",
			"latitude": 51.75222, "longitude": -1.25596,
			"country_name": "United Kingdom", "name": "Oxford", "id": 2640729, "country_code": "GB"
		}"""
	elif url == 'http://geocoder.demozoo.org/?q=Adlington%2C+Lancashire%2C+England%2C+United+Kingdom':
		raise Exception("Looking up Adlington is not allowed! :-)")
	elif url == 'http://geocoder.demozoo.org/?q=Royston+Vasey':
		body = "[]"
	else:
		raise Exception("No response defined for %s" % req.get_full_url())

	resp = urllib2.addinfourl(StringIO(body), None, req.get_full_url())
	resp.code = 200
	resp.msg = "OK"
	return resp


class MockHTTPHandler(urllib2.HTTPHandler):
	def http_open(self, req):
		return mock_response(req)


mock_opener = urllib2.build_opener(MockHTTPHandler)
urllib2.install_opener(mock_opener)
