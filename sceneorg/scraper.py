import urllib2
from BeautifulSoup import BeautifulSoup

user_agent = 'Demozoo/2.0 (gasman@raww.org; http://demozoo.org/)'


def scrape_dir(url):
	req = urllib2.Request(url, None, {'User-Agent': user_agent})
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page, fromEncoding="ISO-8859-1")

	files = []
	for entry in soup.findAll('td', 'filelistentry'):
		if entry.find('img')['src'] == 'img/icons/parent.gif':
			continue
		is_dir = (entry.find('img')['src'] == 'img/icons/dir.gif')
		filename = entry.find('td', 'browseleft').text

		files.append((filename, is_dir))

	return files


def scrape_new_files_dir(url):
	req = urllib2.Request(url, None, {'User-Agent': user_agent})
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page, fromEncoding="ISO-8859-1")

	files = []
	for entry in soup.findAll('td', 'newfile'):
		if entry.find('img')['src'] == 'img/icons/parent.gif':
			continue
		is_dir = (entry.find('img')['src'] == 'img/icons/dir.gif')
		filename = entry.find('td', 'newfilesleft').text

		files.append((filename, is_dir))

	return files
