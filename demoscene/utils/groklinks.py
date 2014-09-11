# coding=utf-8
import re
import urlparse
import urllib
from django.utils.html import escape


class BaseUrl():
	def __init__(self, param):
		self.param = param

	tests = [
		lambda urlstring, url: urlstring  # always match, return full url
	]
	canonical_format = "%s"

	@classmethod
	def extract_param(cls, *args):
		for test in cls.tests:
			m = test(*args)
			if m != None:
				return m

	@classmethod
	def match(cls, *args):
		param = cls.extract_param(*args)
		if param != None:
			return cls(param)

	def __unicode__(self):
		return self.canonical_format % self.param

	def __str__(self):
		return unicode(self).encode('utf-8')

	html_link_class = "website"
	html_link_text = "WWW"
	html_title_format = "%s website"

	def as_html(self, subject):
		return '<a href="%s" class="%s" title="%s">%s</a>' % (
			escape(str(self)), escape(self.html_link_class),
			escape(self.html_title_format % subject),
			escape(self.html_link_text)
		)

	def as_download_link(self):
		hostname = urlparse.urlparse(str(self)).hostname
		return '<div class="primary"><a href="%s">Download (%s)</a></div>' % (
			escape(str(self)), escape(hostname)
		)

	@property
	def download_url(self):
		# gives the most suitable URL for actually downloading the item. Override this
		# in cases where the 'master' URL is not a direct download (e.g. scene.org)
		return str(self)



def regex_match(pattern, flags=None):
	regex = re.compile(pattern, flags)

	def match_fn(urlstring, url):
		m = regex.match(urlstring)
		if m:
			return m.group(1)
	return match_fn


def querystring_match(pattern, varname, flags=None, othervars={}):
	regex = re.compile(pattern, flags)

	def match_fn(urlstring, url):
		if regex.match(urlstring):
			querystring = urlparse.parse_qs(url.query)
			try:
				for (key, val) in othervars.items():
					if querystring[key][0] != val:
						return None
				return querystring[varname][0]
			except KeyError:
				return None
	return match_fn


class TwitterAccount(BaseUrl):
	canonical_format = "http://twitter.com/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?twitter\.com/#!/([^/]+)', re.I),
		regex_match(r'https?://(?:www\.)?twitter\.com/([^/]+)', re.I),
	]
	html_link_class = "twitter"
	html_link_text = "Twitter"
	html_title_format = "%s on Twitter"


class SceneidAccount(BaseUrl):
	canonical_format = "http://www.pouet.net/user.php?who=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?pouet\.net/user\.php', 'who', re.I),
	]
	html_link_class = "pouet"
	html_link_text = u"Pouët"
	html_title_format = u"%s on Pouët"


class PouetGroup(BaseUrl):
	canonical_format = "http://www.pouet.net/groups.php?which=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?pouet\.net/groups\.php', 'which', re.I),
	]
	html_link_class = "pouet"
	html_link_text = u"Pouët"
	html_title_format = u"%s on Pouët"


class PouetProduction(BaseUrl):
	canonical_format = "http://www.pouet.net/prod.php?which=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?pouet\.net/prod\.php', 'which', re.I),
	]
	html_link_class = "pouet"
	html_link_text = u"Pouët"
	html_title_format = u"%s on Pouët"


class SlengpungUser(BaseUrl):
	canonical_format = "http://www.slengpung.com/?userid=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?slengpung\.com/v3/show_user\.php', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?slengpung\.com/', 'userid', re.I),
	]
	html_link_class = "slengpung"
	html_link_text = "Slengpung"
	html_title_format = "%s on Slengpung"


class AmpAuthor(BaseUrl):
	canonical_format = "http://amp.dascene.net/detail.php?view=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?amp\.dascene\.net/detail\.php', 'view', re.I),
	]
	html_link_class = "amp"
	html_link_text = "AMP"
	html_title_format = "%s on Amiga Music Preservation"


class CsdbScener(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/scener/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/scener/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/scener/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"


class CsdbGroup(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/group/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/group/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/group/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"


class CsdbRelease(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/release/?id=%s"
	tests = [
		# need to include the ? in the match so that we don't also match /release/download.php, which is totally different...
		querystring_match(r'https?://noname\.c64\.org/csdb/release/\?', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/release/\?', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"


class CsdbMusic(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/sid/?id=%s"
	tests = [
		# need to include the ? in the match so that we don't also match /release/download.php, which is totally different...
		querystring_match(r'https?://noname\.c64\.org/csdb/sid/\?', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/sid/\?', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"


class NectarineArtist(BaseUrl):
	canonical_format = "https://www.scenemusic.net/demovibes/artist/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/artist/(\d+)', re.I),
	]
	html_link_class = "nectarine"
	html_link_text = "Nectarine"
	html_title_format = "%s on Nectarine Demoscene Radio"


class NectarineSong(BaseUrl):
	canonical_format = "https://www.scenemusic.net/demovibes/song/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/song/(\d+)', re.I),
	]
	html_link_class = "nectarine"
	html_link_text = "Nectarine"
	html_title_format = "%s on Nectarine Demoscene Radio"


class BitjamAuthor(BaseUrl):
	canonical_format = "http://www.bitfellas.org/e107_plugins/radio/radio.php?search&q=%s&type=author&page=1"
	tests = [
		querystring_match(r'https?://(?:www\.)?bitfellas\.org/e107_plugins/radio/radio\.php\?search', 'q', re.I),
	]
	html_link_class = "bitjam"
	html_link_text = "BitJam"
	html_title_format = "%s on BitJam"


class BitjamSong(BaseUrl):
	canonical_format = "http://www.bitfellas.org/e107_plugins/radio/radio.php?info&id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?bitfellas\.org/e107_plugins/radio/radio\.php\?info', 'id', re.I),
	]
	html_link_class = "bitjam"
	html_link_text = "BitJam"
	html_title_format = "%s on BitJam"


class ArtcityArtist(BaseUrl):
	canonical_format = "http://artcity.bitfellas.org/index.php?a=artist&id=%s"
	tests = [
		querystring_match(r'https?://artcity\.bitfellas\.org/index\.php', 'id', re.I, othervars={'a': 'artist'}),
	]
	html_link_class = "artcity"
	html_link_text = "ArtCity"
	html_title_format = "%s on ArtCity"


class DeviantartUser(BaseUrl):
	canonical_format = "http://%s.deviantart.com"
	tests = [
		regex_match(r'https?://(.*)\.deviantart\.com/?', re.I),
	]
	html_link_class = "deviantart"
	html_link_text = "deviantART"
	html_title_format = "%s on deviantART"


class MobygamesDeveloper(BaseUrl):
	canonical_format = "http://www.mobygames.com/developer/sheet/view/developerId,%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?mobygames\.com/developer/sheet/view/developerId\,(\d+)', re.I),
	]
	html_link_class = "mobygames"
	html_link_text = "MobyGames"
	html_title_format = "%s on MobyGames"


class AsciiarenaArtist(BaseUrl):
	canonical_format = "http://www.asciiarena.com/info_artist.php?artist=%s&sort_by=filename"
	tests = [
		querystring_match(r'https?://(?:www\.)?asciiarena\.com/info_artist\.php', 'artist', re.I),
	]
	html_link_class = "asciiarena"
	html_link_text = "AsciiArena"
	html_title_format = "%s on AsciiArena"


class AsciiarenaCrew(BaseUrl):
	canonical_format = "http://www.asciiarena.com/info_crew.php?crew=%s&sort_by=filename"
	tests = [
		querystring_match(r'https?://(?:www\.)?asciiarena\.com/info_crew\.php', 'crew', re.I),
	]
	html_link_class = "asciiarena"
	html_link_text = "AsciiArena"
	html_title_format = "%s on AsciiArena"


class AsciiarenaRelease(BaseUrl):
	canonical_format = "http://www.asciiarena.com/info_release.php?filename=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?asciiarena\.com/info_release\.php', 'filename', re.I),
	]
	html_link_class = "asciiarena"
	html_link_text = "AsciiArena"
	html_title_format = "%s on AsciiArena"


class ScenesatAct(BaseUrl):
	canonical_format = "http://scenesat.com/act/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?scenesat\.com/act/(\d+)', re.I),
	]
	html_link_class = "scenesat"
	html_link_text = "SceneSat"
	html_title_format = "%s on SceneSat Radio"


class ScenesatTrack(BaseUrl):
	canonical_format = "http://scenesat.com/track/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?scenesat\.com/track/(\d+)', re.I),
	]
	html_link_class = "scenesat"
	html_link_text = "SceneSat"
	html_title_format = "%s on SceneSat Radio"


class ZxdemoAuthor(BaseUrl):
	canonical_format = "http://zxdemo.org/author.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?zxdemo\.org/author\.php', 'id', re.I),
	]
	html_link_class = "zxdemo"
	html_link_text = "ZXdemo"
	html_title_format = "%s on zxdemo.org"


class ZxdemoItem(BaseUrl):
	canonical_format = "http://zxdemo.org/item.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?zxdemo\.org/item\.php', 'id', re.I),
	]
	html_link_class = "zxdemo"
	html_link_text = "ZXdemo"
	html_title_format = "%s on zxdemo.org"


class BitworldDemo(BaseUrl):
	canonical_format = "http://bitworld.bitfellas.org/demo.php?id=%s"
	tests = [
		querystring_match(r'https?://bitworld\.bitfellas\.org/demo\.php', 'id', re.I),
	]
	html_link_class = "bitworld"
	html_link_text = "BitWorld"
	html_title_format = "%s on BitWorld"


class KestraBitworldRelease(BaseUrl):
	canonical_format = "http://janeway.exotica.org.uk/release.php?id=%s"
	tests = [
		querystring_match(r'https?://janeway\.exotica\.org\.uk/release\.php', 'id', re.I),
	]
	html_link_class = "kestra_bitworld"
	html_link_text = "Kestra BitWorld"
	html_title_format = "%s on Kestra BitWorld"


class KestraBitworldAuthor(BaseUrl):
	canonical_format = "http://janeway.exotica.org.uk/author.php?id=%s"
	tests = [
		querystring_match(r'https?://janeway\.exotica\.org\.uk/author\.php', 'id', re.I),
	]
	html_link_class = "kestra_bitworld"
	html_link_text = "Kestra BitWorld"
	html_title_format = "%s on Kestra BitWorld"


class KestraBitworldParty(BaseUrl):
	canonical_format = "http://janeway.exotica.org.uk/party.php?id=%s"
	tests = [
		querystring_match(r'https?://janeway\.exotica\.org\.uk/party\.php', 'id', re.I),
	]
	html_link_class = "kestra_bitworld"
	html_link_text = "Kestra BitWorld"
	html_title_format = "%s on Kestra BitWorld"


class SceneOrgFile(BaseUrl):

	# custom test for file_dl.php URLs, of the format:
	# http://www.scene.org/file_dl.php?url=ftp://ftp.scene.org/pub/parties/2009/stream09/in4k/moldtype.zip&id=523700
	file_dl_regex = re.compile(r'https?://(?:www\.)?scene\.org/file_dl\.php', re.I)

	def file_dl_match(urlstring, url):
		if SceneOrgFile.file_dl_regex.match(urlstring):
			# link is a file_dl.php link; extract the inner url, then recursively match on that
			querystring = urlparse.parse_qs(url.query)
			try:
				inner_url_string = querystring['url'][0]
				inner_url = urlparse.urlparse(inner_url_string)
				return SceneOrgFile.extract_param(inner_url_string, inner_url)
			except KeyError:
				return None

	tests = [
		file_dl_match,
		querystring_match(r'https?://(?:www\.)?scene\.org/file\.php', 'file', re.I),
		regex_match(r'ftp://(?:ftp\.)?(?:nl\.)?scene\.org/pub(/.*)', re.I),
		regex_match(r'ftp://(?:ftp\.)?(?:nl\.)?scene\.org(/mirrors/.*)', re.I),
		regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*)', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*)', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*)', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*)', re.I),
		regex_match(r'http://(?:http\.)?de\.scene\.org/pub(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*)', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org(/.*)', re.I),
		regex_match(r'http://http\.fr\.scene\.org(/.*)', re.I),
		regex_match(r'http://http\.hu\.scene\.org(/.*)', re.I),
	]

	def __unicode__(self):
		return u"https://www.scene.org/file.php?file=%s&fileinfo" % urllib.quote(self.param.encode('iso-8859-1'))
	html_link_class = "sceneorg"
	html_link_text = "scene.org"
	html_title_format = "%s on scene.org"

	@property
	def mirror_links(self):
		links = [
			'<li><a class="country_nl" href="%s">nl</a></li>' % escape(self.nl_url),
#			'<li><a href="%s" class="country_de">de/ftp</a></li>' % escape(self.de_ftp_url),
#			'<li><a href="%s" class="country_de">de/http</a></li>' % escape(self.de_http_url),
#			'<li><a href="%s" class="country_us">us/ftp</a></li>' % escape(self.us_ftp_url),
			'<li><a href="%s" class="country_us">us</a></li>' % escape(self.us_http_url),
		]
		if not self.param.startswith('/mirrors/'):
			links += [
				'<li><a class="country_no" href="%s">no</a></li>' % escape(self.no_url),
				# '<li><a class="country_jp" href="%s">jp</a></li>' % escape(self.jp_url),
			]
			#if not self.param.startswith('/resources/'):
			#	links += [
			#		'<li><a class="country_hu" href="%s">hu</a></li>' % escape(self.hu_url),
			#	]
		if self.param.startswith('/mags/') or self.param.startswith('/parties/') or self.param.startswith('/resources/'):
			links += [
				'<li><a class="country_fr" href="%s">fr</a></li>' % escape(self.fr_url),
			]

		return links

	@property
	def nl_url(self):
		return "ftp://ftp.scene.org/pub%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def download_url(self):
		return self.nl_url

	@property
	def no_url(self):
		return "ftp://ftp.no.scene.org/scene.org%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def jp_url(self):
		return "ftp://ftp.jp.scene.org/pub/demos/scene%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def de_ftp_url(self):
		return "ftp://ftp.de.scene.org/pub%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def de_http_url(self):
		return "http://http.de.scene.org/pub%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def us_ftp_url(self):
		return "ftp://ftp.us.scene.org/pub/scene.org%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def us_http_url(self):
		return "http://http.us.scene.org/pub/scene.org%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def fr_url(self):
		return "http://http.fr.scene.org%s" % urllib.quote(self.param.encode('iso-8859-1'))

	@property
	def hu_url(self):
		return "http://http.hu.scene.org%s" % urllib.quote(self.param.encode('iso-8859-1'))

	def as_download_link(self):
		mirrors_html = ' '.join(self.mirror_links)
		return '''
			<div class="primary"><a href="%s">Download from scene.org</a></div>
			<div class="secondary">mirrors: <ul class="download_mirrors">%s</ul></div>
		''' % (
			escape(str(self)), mirrors_html
		)


class AmigascneFile(BaseUrl):
	canonical_format = "http://ftp.amigascne.org/pub/amiga%s"
	tests = [
		regex_match(r'(?:http|ftp)://ftp\.amigascne\.org/pub/amiga(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub/mirrors/amigascne(/.*)', re.I),
		regex_match(r'http://(?:http\.)?de\.scene\.org/pub/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org/mirrors/amigascne(/.*)', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org/mirrors/amigascne(/.*)', re.I),
	]
	html_link_class = "amigascne"
	html_link_text = "amigascne.org"
	html_title_format = "%s on amigascne.org"

	@property
	def mirror_links(self):
		links = [
			'<li><a class="country_nl" href="%s">nl</a></li>' % escape(self.nl_url),
			#'<li><a href="%s" class="country_de">de/ftp</a></li>' % escape(self.de_ftp_url),
			#'<li><a href="%s" class="country_de">de/http</a></li>' % escape(self.de_http_url),
			#'<li><a href="%s" class="country_us">us/ftp</a></li>' % escape(self.us_ftp_url),
			'<li><a href="%s" class="country_us">us</a></li>' % escape(self.us_http_url),
		]

		return links

	@property
	def nl_url(self):
		return "ftp://ftp.scene.org/pub/mirrors/amigascne%s" % self.param

	@property
	def de_ftp_url(self):
		return "ftp://ftp.de.scene.org/pub/mirrors/amigascne%s" % self.param

	@property
	def de_http_url(self):
		return "http://http.de.scene.org/pub/mirrors/amigascne%s" % self.param

	@property
	def us_ftp_url(self):
		return "ftp://ftp.us.scene.org/pub/scene.org/mirrors/amigascne%s" % self.param

	@property
	def us_http_url(self):
		return "http://http.us.scene.org/pub/scene.org/mirrors/amigascne%s" % self.param

	def as_download_link(self):
		mirrors_html = ' '.join(self.mirror_links)
		return '''
			<div class="primary"><a href="%s">Download from amigascne.org</a></div>
			<div class="secondary">mirrors: <ul class="download_mirrors">%s</ul></div>
		''' % (
			escape(str(self)), mirrors_html
		)


class PaduaOrgFile(BaseUrl):
	canonical_format = "ftp://ftp.padua.org/pub/c64%s"
	tests = [
		regex_match(r'ftp://ftp\.padua\.org/pub/c64(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/mirrors/padua(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub/mirrors/padua(/.*)', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub/mirrors/padua(/.*)', re.I),
		regex_match(r'http://(?:http\.)?de\.scene\.org/pub/mirrors/padua(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org/mirrors/padua(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org/mirrors/padua(/.*)', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org/mirrors/padua(/.*)', re.I),
	]
	html_link_class = "padua"
	html_link_text = "padua.org"
	html_title_format = "%s on ftp.padua.org"

	@property
	def mirror_links(self):
		links = [
			'<li><a class="country_nl" href="%s">nl</a></li>' % escape(self.nl_url),
			#'<li><a href="%s" class="country_de">de/ftp</a></li>' % escape(self.de_ftp_url),
			#'<li><a href="%s" class="country_de">de/http</a></li>' % escape(self.de_http_url),
			#'<li><a href="%s" class="country_us">us/ftp</a></li>' % escape(self.us_ftp_url),
			'<li><a href="%s" class="country_us">us</a></li>' % escape(self.us_http_url),
		]

		return links

	@property
	def nl_url(self):
		return "ftp://ftp.scene.org/pub/mirrors/padua%s" % self.param

	@property
	def de_ftp_url(self):
		return "ftp://ftp.de.scene.org/pub/mirrors/padua%s" % self.param

	@property
	def de_http_url(self):
		return "http://http.de.scene.org/pub/mirrors/padua%s" % self.param

	@property
	def us_ftp_url(self):
		return "ftp://ftp.us.scene.org/pub/scene.org/mirrors/padua%s" % self.param

	@property
	def us_http_url(self):
		return "http://http.us.scene.org/pub/scene.org/mirrors/padua%s" % self.param

	def as_download_link(self):
		mirrors_html = ' '.join(self.mirror_links)
		return '''
			<div class="primary"><a href="%s">Download from padua.org</a></div>
			<div class="secondary">mirrors: <ul class="download_mirrors">%s</ul></div>
		''' % (
			escape(str(self)), mirrors_html
		)


class ModlandFile(BaseUrl):
	canonical_format = "ftp://ftp.modland.com%s"

	# need to fiddle querystring_match to prepend a slash to the matched query param
	def exotica_querystring_match():
		inner_fn = querystring_match(r'https?://files.exotica.org.uk/modland/\?', 'file', re.I)

		def wrapped_fn(*args):
			result = inner_fn(*args)
			if result is None:
				return None
			else:
				return '/' + result

		return wrapped_fn

	tests = [
		regex_match(r'ftp://ftp\.modland\.com(/.*)', re.I),
		regex_match(r'ftp://hangar18\.exotica\.org\.uk/modland(/.*)', re.I),
		regex_match(r'ftp://aero.exotica.org.uk/pub/mirrors/modland(/.*)', re.I),
		regex_match(r'ftp://modland\.ziphoid\.com(/.*)', re.I),
		regex_match(r'ftp://ftp\.amigascne\.org/mirrors/ftp\.modland\.com(/.*)', re.I),
		regex_match(r'ftp://ftp\.rave\.ca(/.*)', re.I),
		regex_match(r'ftp://modland\.mindkiller\.com/modland(/.*)', re.I),
		exotica_querystring_match(),
	]
	html_link_class = "modland"
	html_link_text = "Modland"
	html_title_format = "%s on Modland"

	@property
	def mirror_links(self):
		links = [
			'<li><a class="country_uk" href="%s">uk</a></li>' % escape(self.uk_url),
			'<li><a href="%s" class="country_se">se</a></li>' % escape(self.se_url),
			'<li><a href="%s" class="country_us">us</a></li>' % escape(self.us_url),
			'<li><a href="%s" class="country_ca">ca</a></li>' % escape(self.ca_url),
		]

		return links

	@property
	def uk_url(self):
		return "ftp://hangar18.exotica.org.uk/modland%s" % self.param

	@property
	def se_url(self):
		return "ftp://modland.ziphoid.com%s" % self.param

	@property
	def us_url(self):
		return "ftp://ftp.amigascne.org/mirrors/ftp.modland.com%s" % self.param

	@property
	def ca_url(self):
		return "ftp://ftp.rave.ca%s" % self.param

	def as_download_link(self):
		mirrors_html = ' '.join(self.mirror_links)
		return '''
			<div class="primary"><a href="%s">Download from Modland</a></div>
			<div class="secondary">mirrors: <ul class="download_mirrors">%s</ul></div>
		''' % (
			escape(str(self)), mirrors_html
		)


class UntergrundFile(BaseUrl):
	canonical_format = "ftp://ftp.untergrund.net%s"
	tests = [
		regex_match(r'ftp://ftp\.untergrund\.net(/.*)', re.I),
	]
	html_link_class = "untergrund"
	html_link_text = "untergrund.net"
	html_title_format = "%s on untergrund.net"


class DemopartyNetParty(BaseUrl):
	canonical_format = "http://www.demoparty.net/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?demoparty\.net/([^/]+)', re.I),
	]
	html_link_class = "demoparty_net"
	html_link_text = "demoparty.net"
	html_title_format = "%s on demoparty.net"


class LanyrdEvent(BaseUrl):
	canonical_format = "http://lanyrd.com/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?lanyrd\.com/(\d+/[^/]+)', re.I),
	]
	html_link_class = "lanyrd"
	html_link_text = "Lanyrd"
	html_title_format = "%s on Lanyrd"


class SlengpungParty(BaseUrl):
	canonical_format = "http://www.slengpung.com/?eventid=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?slengpung\.com/v3/parties\.php', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?slengpung\.com/', 'eventid', re.I),
	]
	html_link_class = "slengpung"
	html_link_text = "Slengpung"
	html_title_format = "%s on Slengpung"


class PouetParty(BaseUrl):
	def match_pouet_party(urlstring, url):
		regex = re.compile(r'https?://(?:www\.)?pouet\.net/party\.php', re.I)
		if regex.match(urlstring):
			querystring = urlparse.parse_qs(url.query)
			try:
				return "%s/%s" % (querystring['which'][0], querystring['when'][0])
			except KeyError:
				return None

	tests = [match_pouet_party]

	def __unicode__(self):
		(id, year) = self.param.split('/')
		return u"http://www.pouet.net/party.php?which=%s&when=%s" % (id, year)
	html_link_class = "pouet"
	html_link_text = u"Pouët"
	html_title_format = u"%s on Pouët"


class BitworldParty(BaseUrl):
	canonical_format = "http://bitworld.bitfellas.org/party.php?id=%s"
	tests = [
		querystring_match(r'https?://bitworld\.bitfellas\.org/party\.php', 'id', re.I),
	]
	html_link_class = "bitworld"
	html_link_text = "BitWorld"
	html_title_format = "%s on BitWorld"


class CsdbEvent(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/event/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/event/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/event/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"


class BreaksAmigaParty(BaseUrl):
	canonical_format = "http://arabuusimiehet.com/break/amiga/index.php?mode=party&partyid=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?arabuusimiehet\.com/break/amiga/index\.php', 'partyid', re.I, othervars={'mode': 'party'}),
	]
	html_link_class = "breaks_amiga"
	html_link_text = "Break's Amiga Collection"
	html_title_format = "%s on Break's Amiga Collection"


class SceneOrgFolder(BaseUrl):
	tests = [
		querystring_match(r'https?://(?:www\.)?scene\.org/dir\.php', 'dir', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org(/mirrors/.*/)$', re.I),
		regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*/)$', re.I),
		regex_match(r'http://(?:http\.)?de\.scene\.org/pub(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*/)$', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org(/.*/)$', re.I),
		regex_match(r'http://http\.fr\.scene\.org(/.*/)$', re.I),
	]

	def __unicode__(self):
		return u"https://www.scene.org/dir.php?dir=%s" % urllib.quote(self.param.encode('iso-8859-1'))
	html_link_class = "sceneorg"
	html_link_text = "scene.org"
	html_title_format = "%s on scene.org"


class ZxdemoParty(BaseUrl):
	canonical_format = "http://zxdemo.org/party.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?zxdemo\.org/party\.php', 'id', re.I),
	]
	html_link_class = "zxdemo"
	html_link_text = "ZXdemo"
	html_title_format = "%s on zxdemo.org"


class YoutubeVideo(BaseUrl):
	canonical_format = "http://www.youtube.com/watch?v=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?youtube\.com/watch', 'v', re.I),
		regex_match(r'https?://(?:www\.)?youtube\.com/embed/([^/]+)', re.I),
		regex_match(r'https?://(?:www\.)?youtu\.be/([^/]+)', re.I),
	]
	html_link_class = "youtube"
	html_link_text = "YouTube"
	html_title_format = "%s on YouTube"
	is_streaming_video = True


class YoutubeUser(BaseUrl):
	canonical_format = "http://www.youtube.com/user/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?youtube\.com/user/([^\/\?]+)', re.I),
	]
	html_link_class = "youtube"
	html_link_text = "YouTube"
	html_title_format = "%s on YouTube"


class YoutubeChannel(BaseUrl):
	canonical_format = "http://www.youtube.com/channel/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?youtube\.com/channel/([^\/\?]+)', re.I),
	]
	html_link_class = "youtube"
	html_link_text = "YouTube"
	html_title_format = "%s on YouTube"


class VimeoVideo(BaseUrl):
	canonical_format = "http://vimeo.com/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?vimeo\.com/(\d+)', re.I),
	]
	html_link_class = "vimeo"
	html_link_text = "Vimeo"
	html_title_format = "%s on Vimeo"
	is_streaming_video = True


class DemosceneTvVideo(BaseUrl):
	canonical_format = "http://demoscene.tv/page.php?id=172&vsmaction=view_prod&id_prod=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?demoscene\.tv/prod\.php', 'id_prod', re.I),
		querystring_match(r'https?://(?:www\.)?demoscene\.tv/page\.php', 'id_prod', re.I, othervars={'id': '172', 'vsmaction': 'view_prod'}),
	]
	html_link_class = "demoscene_tv"
	html_link_text = "Demoscene.tv"
	html_title_format = "%s on Demoscene.tv"
	is_streaming_video = True


class CappedVideo(BaseUrl):
	canonical_format = "http://capped.tv/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?capped\.tv/([-_\w]+)', re.I),
	]
	html_link_class = "capped"
	html_link_text = "Capped.TV"
	html_title_format = "%s on Capped.TV"
	is_streaming_video = True


class DhsVideoDbVideo(BaseUrl):
	canonical_format = "http://dhs.nu/video.php?ID=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?dhs\.nu/video.php', 'ID', re.I),
	]
	html_link_class = "dhs_videodb"
	html_link_text = "DHS VideoDB"
	html_title_format = "%s on DHS VideoDB"


class FacebookPage(BaseUrl):
	canonical_format = "http://www.facebook.com/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?facebook\.com/(.+)', re.I),
	]
	html_link_class = "facebook"
	html_link_text = "Facebook"
	html_title_format = "%s on Facebook"


class GooglePlusPage(BaseUrl):
	canonical_format = "https://plus.google.com/%s/"
	tests = [
		regex_match(r'https?://plus\.google\.com/(\d+)', re.I),
	]
	html_link_class = "googleplus"
	html_link_text = "Google+"
	html_title_format = "%s on Google+"


class GooglePlusEvent(BaseUrl):
	canonical_format = "https://plus.google.com/u/0/events/%s"
	tests = [
		regex_match(r'https?://plus\.google\.com/u/0/events/(\w+)', re.I),
	]
	html_link_class = "googleplus"
	html_link_text = "Google+"
	html_title_format = "%s on Google+"


class SoundcloudUser(BaseUrl):
	canonical_format = "http://soundcloud.com/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?soundcloud\.com/([^\/]+)', re.I),
	]
	html_link_class = "soundcloud"
	html_link_text = "SoundCloud"
	html_title_format = "%s on SoundCloud"


class SoundcloudTrack(BaseUrl):
	canonical_format = "http://soundcloud.com/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?soundcloud\.com/([^\/]+/[^\/]+)', re.I),
	]
	html_link_class = "soundcloud"
	html_link_text = "SoundCloud"
	html_title_format = "%s on SoundCloud"


class DiscogsEntry(BaseUrl):  # for use as an abstract superclass
	html_link_class = "discogs"
	html_link_text = "Discogs"
	html_title_format = "%s on Discogs"


class DiscogsArtist(DiscogsEntry):
	canonical_format = "http://www.discogs.com/artist/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?discogs\.com/artist/(.+)', re.I),
	]


class DiscogsLabel(DiscogsEntry):
	canonical_format = "http://www.discogs.com/label/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?discogs\.com/label/(.+)', re.I),
	]


class DiscogsRelease(DiscogsEntry):
	def match_discogs_release(urlstring, url):
		regex = re.compile(r'https?://(?:www\.)?discogs\.com/([^\/]+)/release/(\d+)', re.I)
		match = regex.match(urlstring)
		if match:
			slug, id = match.groups()
			return "%s/%s" % (id, slug)

	tests = [match_discogs_release]

	def __unicode__(self):
		(id, slug) = self.param.split('/')
		return u"http://www.discogs.com/%s/release/%s" % (slug, id)


class ModarchiveMember(BaseUrl):
	canonical_format = "http://modarchive.org/member.php?%s"
	tests = [
		regex_match(r'https?://(?:www\.)?modarchive\.org/member\.php\?(\d+)', re.I),
		querystring_match(r'https?://(?:www\.)?modarchive\.org/index\.php', 'query', re.I, othervars={'request': 'view_profile'}),
	]
	html_link_class = "modarchive"
	html_link_text = "ModArchive"
	html_title_format = "%s on The Mod Archive"


class ModarchiveModule(BaseUrl):
	canonical_format = "http://modarchive.org/module.php?%s"
	tests = [
		regex_match(r'https?://(?:www\.)?modarchive\.org/module\.php\?(\d+)', re.I),
		querystring_match(r'https?://(?:www\.)?modarchive\.org/index\.php', 'query', re.I, othervars={'request': 'view_by_moduleid'}),
	]
	html_link_class = "modarchive"
	html_link_text = "ModArchive"
	html_title_format = "%s on The Mod Archive"


class WikipediaPage(BaseUrl):
	canonical_format = "%s"  # entire URL is stored as parameter, to cover all language domains
	tests = [
		regex_match(r'(https?://\w+\.wikipedia\.org/.*)', re.I),
	]
	html_link_class = "wikipedia"
	html_link_text = "Wikipedia"
	html_title_format = "%s on Wikipedia"


class SpeccyWikiPage(BaseUrl):
	canonical_format = "http://speccy.info/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?speccy.info/(.+)', re.I),
	]
	html_link_class = "speccywiki"
	html_link_text = "SpeccyWiki"
	html_title_format = "%s on SpeccyWiki"


class AtarimaniaPage(BaseUrl):
	canonical_format = "http://www.atarimania.com/%s.html"
	tests = [
		regex_match(r'https?://(?:www\.)?atarimania.com/(.+)\.html', re.I),
	]
	html_link_class = "atarimania"
	html_link_text = "Atarimania"
	html_title_format = "%s on Atarimania"


class PushnpopEntry(BaseUrl):  # for use as an abstract superclass
	html_link_class = "pushnpop"
	html_link_text = "Push'n'Pop"
	html_title_format = "%s on Push'n'Pop"


class PushnpopProduction(PushnpopEntry):
	canonical_format = "http://pushnpop.net/prod-%s.html"
	tests = [
		regex_match(r'https?://(?:www\.)?pushnpop\.net/prod-(\d+)\.html', re.I),
	]


class PushnpopParty(PushnpopEntry):
	canonical_format = "http://pushnpop.net/parties-%s.html"
	tests = [
		regex_match(r'https?://(?:www\.)?pushnpop\.net/parties-(\d+)\.html', re.I),
	]


class PushnpopGroup(PushnpopEntry):
	canonical_format = "http://pushnpop.net/group-%s.html"
	tests = [
		regex_match(r'https?://(?:www\.)?pushnpop\.net/group-(\d+)\.html', re.I),
	]


class PushnpopProfile(PushnpopEntry):
	canonical_format = "http://pushnpop.net/profile-%s.html"
	tests = [
		regex_match(r'https?://(?:www\.)?pushnpop\.net/profile-(\d+)\.html', re.I),
	]


class ZxArtEntry(BaseUrl):  # for use as an abstract superclass
	html_link_class = "zxart"
	html_link_text = "ZXArt"
	html_title_format = "%s on ZXArt"


class ZxArtArtist(ZxArtEntry):
	canonical_format = "http://zxart.ee/eng/graphics/authors/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/authors/([^\/]+/[^\/]+)/', re.I),
		regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/avtory/([^\/]+/[^\/]+)/', re.I),
	]


class ZxArtMusician(ZxArtEntry):
	canonical_format = "http://zxart.ee/eng/music/authors/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/authors/([^\/]+/[^\/]+)/', re.I),
		regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/avtory/([^\/]+/[^\/]+)/', re.I),
	]


class ZxArtPicture(ZxArtEntry):
	canonical_format = "http://zxart.ee/eng/graphics/authors/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/authors/([^\/]+/[^\/]+/[^\/]+)/', re.I),
		regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/avtory/([^\/]+/[^\/]+/[^\/]+)/', re.I),
	]


class ZxArtMusic(ZxArtEntry):
	canonical_format = "http://zxart.ee/eng/music/authors/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/authors/([^\/]+/[^\/]+/[^\/]+)/', re.I),
		regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/avtory/([^\/]+/[^\/]+/[^\/]+)/', re.I),
	]


class ZxArtPartyGraphics(ZxArtEntry):
	canonical_format = "http://zxart.ee/eng/graphics/parties/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/parties/([^\/]+/[^\/]+)/', re.I),
		regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/pati/([^\/]+/[^\/]+)/', re.I),
	]


class ZxArtPartyMusic(ZxArtEntry):
	canonical_format = "http://zxart.ee/eng/music/parties/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/parties/([^\/]+/[^\/]+)/', re.I),
		regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/pati/([^\/]+/[^\/]+)/', re.I),
	]


class HallOfLightEntry(BaseUrl):  # for use as an abstract superclass
	html_link_class = "hall_of_light"
	html_link_text = "Hall Of Light"
	html_title_format = "%s on Hall Of Light"


class HallOfLightGame(HallOfLightEntry):
	canonical_format = "http://hol.abime.net/%s"
	tests = [
		regex_match(r'https?://hol\.abime\.net/(\d+)', re.I),
	]


class HallOfLightArtist(HallOfLightEntry):
	canonical_format = "http://hol.abime.net/hol_search.php?N_ref_artist=%s"
	tests = [
		querystring_match(r'https?://hol\.abime\.net/hol_search\.php', 'N_ref_artist', re.I),
	]


class SpotifyArtist(BaseUrl):
	canonical_format = "http://open.spotify.com/artist/%s"
	tests = [
		regex_match(r'https?://open\.spotify\.com/artist/(\w+)', re.I),
	]
	html_link_class = "spotify"
	html_link_text = "Spotify"
	html_title_format = "%s on Spotify"


class SpotifyTrack(BaseUrl):
	canonical_format = "https://play.spotify.com/track/%s"
	tests = [
		regex_match(r'https?://play\.spotify\.com/track/(\w+)', re.I),
	]
	html_link_class = "spotify"
	html_link_text = "Spotify"
	html_title_format = "%s on Spotify"


class GithubAccount(BaseUrl):
	canonical_format = "https://github.com/%s"
	tests = [
		regex_match(r'https?://github\.com/([^\/]+)/?$', re.I),
	]
	html_link_class = "github"
	html_link_text = "GitHub"
	html_title_format = "%s on GitHub"


class GithubRepo(BaseUrl):
	canonical_format = "https://github.com/%s"
	tests = [
		regex_match(r'https?://github\.com/([^\/]+/[^\/]+)/?$', re.I),
	]
	html_link_class = "github"
	html_link_text = "GitHub"
	html_title_format = "%s on GitHub"


class InternetArchivePage(BaseUrl):
	canonical_format = "https://archive.org/details/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?archive.org/details/(.+)', re.I),
	]
	html_link_class = "internetarchive"
	html_link_text = "Internet Archive"
	html_title_format = "%s on the Internet Archive"


class WaybackMachinePage(BaseUrl):
	canonical_format = "https://web.archive.org/web/%s"
	tests = [
		regex_match(r'https?://web\.archive.org/web/(.+)', re.I),
	]
	html_link_class = "waybackmachine"
	html_link_text = "Wayback Machine"
	html_title_format = "%s on the Wayback Machine"


RELEASER_LINK_TYPES = [
	TwitterAccount, SceneidAccount, SlengpungUser, AmpAuthor,
	CsdbScener, CsdbGroup, NectarineArtist, BitjamAuthor, ArtcityArtist,
	MobygamesDeveloper, AsciiarenaArtist, AsciiarenaCrew, PouetGroup,
	ScenesatAct, ZxdemoAuthor, FacebookPage,
	PushnpopGroup, PushnpopProfile, SceneOrgFolder,
	GooglePlusPage, SoundcloudUser, YoutubeUser, YoutubeChannel,
	DeviantartUser, ModarchiveMember, WikipediaPage,
	SpeccyWikiPage, DiscogsArtist, DiscogsLabel,
	HallOfLightArtist, SpotifyArtist, KestraBitworldAuthor,
	GithubAccount, GithubRepo, AtarimaniaPage,
	ZxArtArtist, ZxArtMusician, InternetArchivePage,
	WaybackMachinePage, BaseUrl,
]

PRODUCTION_LINK_TYPES = [
	PouetProduction, CsdbRelease, ZxdemoItem, BitworldDemo,
	YoutubeVideo, VimeoVideo, DemosceneTvVideo, CappedVideo, DhsVideoDbVideo,
	AsciiarenaRelease, KestraBitworldRelease,
	ScenesatTrack, ModlandFile, SoundcloudTrack, CsdbMusic, NectarineSong,
	ModarchiveModule, BitjamSong, PushnpopProduction, SpotifyTrack,
	AmigascneFile, PaduaOrgFile,  # sites mirrored by scene.org - must come before SceneOrgFile
	SceneOrgFile, UntergrundFile, GithubAccount, GithubRepo,
	WikipediaPage, SpeccyWikiPage, AtarimaniaPage, HallOfLightGame,
	DiscogsRelease, ZxArtPicture, ZxArtMusic, InternetArchivePage,
	WaybackMachinePage, BaseUrl,
]

PRODUCTION_DOWNLOAD_LINK_TYPES = [
	'AmigascneFile', 'SceneOrgFile', 'UntergrundFile', 'PaduaOrgFile', 'ModlandFile'
]

PRODUCTION_EXTERNAL_LINK_TYPES = [
	'PouetProduction', 'CsdbRelease', 'CsdbMusic', 'ZxdemoItem', 'BitworldDemo', 'YoutubeVideo',
	'VimeoVideo', 'DemosceneTvVideo', 'CappedVideo', 'DhsVideoDbVideo', 'AsciiarenaRelease', 'ScenesatTrack',
	'ModarchiveModule', 'BitjamSong', 'SoundcloudTrack', 'NectarineSong', 'KestraBitworldRelease',
	'PushnpopProduction', 'WikipediaPage', 'SpeccyWikiPage', 'SpotifyTrack',
	'GithubAccount', 'GithubRepo', 'AtarimaniaPage', 'HallOfLightGame', 'DiscogsRelease',
	'ZxArtPicture', 'ZxArtMusic', 'InternetArchivePage', 'WaybackMachinePage',
]

PARTY_LINK_TYPES = [
	DemopartyNetParty, SlengpungParty, PouetParty, BitworldParty,
	CsdbEvent, BreaksAmigaParty, SceneOrgFolder, TwitterAccount, ZxdemoParty,
	PushnpopParty, KestraBitworldParty, YoutubeUser, YoutubeChannel,
	FacebookPage, GooglePlusPage, GooglePlusEvent, LanyrdEvent, WikipediaPage,
	SpeccyWikiPage, ZxArtPartyGraphics, ZxArtPartyMusic, WaybackMachinePage, BaseUrl,
]


def grok_link_by_types(urlstring, link_types):
	url = urlparse.urlparse(urlstring)
	for link_type in link_types:
		link = link_type.match(urlstring, url)
		if link:
			return link


def grok_production_link(urlstring):
	return grok_link_by_types(urlstring, PRODUCTION_LINK_TYPES)
