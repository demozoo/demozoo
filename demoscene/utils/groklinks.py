import re

class BaseUrl():
	def __init__(self, param):
		self.param = param
	
	tests = [
		lambda(url): url # always match, return full url
	]
	canonical_format = "%s"
	
	@classmethod
	def match(cls, url):
		for test in cls.tests:
			m = test(url)
			if m:
				return cls(m)
	
	def __str__(self):
		return self.canonical_format % self.param

def regex_match(pattern, flags = None):
	regex = re.compile(pattern, flags)
	def match_fn(url):
		m = regex.match(url)
		if m:
			return m.group(1)
	return match_fn

class TwitterAccount(BaseUrl):
	canonical_format = "http://twitter.com/%s"
	
	tests = [
		regex_match('https?://(?:www\.)?twitter\.com/#!/([^/]+)', re.I),
		regex_match('https?://(?:www\.)?twitter\.com/([^/]+)', re.I),
	]

def grok_scener_link(url):
	for link_type in [TwitterAccount, BaseUrl]:
		link = link_type.match(url)
		if link:
			return link
