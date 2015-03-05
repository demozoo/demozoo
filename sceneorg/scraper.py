import urllib2
from BeautifulSoup import BeautifulSoup

user_agent = 'Demozoo/2.0 (gasman@raww.org; http://demozoo.org/)'


def scrape_dir(url):
	req = urllib2.Request(url, None, {'User-Agent': user_agent})
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page)

	files = []
	for entry in soup.findAll('li', 'file'):
		try:
			classnames = entry['class'].split(' ')
		except KeyError:
			classnames = []

		if 'parent' in classnames:
			continue
		is_dir = ('directory' in classnames)
		filename = entry.find('span', 'filename').text

		files.append((filename, is_dir, None))

	return files
