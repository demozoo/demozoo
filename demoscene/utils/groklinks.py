# coding=utf-8
import re, urlparse, urllib
from django.utils.html import escape

class BaseUrl():
	def __init__(self, param):
		self.param = param
	
	tests = [
		lambda urlstring, url: urlstring # always match, return full url
	]
	canonical_format = "%s"
	
	@classmethod
	def match(cls, *args):
		for test in cls.tests:
			m = test(*args)
			if m:
				return cls(m)
	
	def __str__(self):
		return self.canonical_format % self.param
	
	html_link_class = "website"
	html_link_text = "WWW"
	html_title_format = "%s website"
	
	def as_html(self, subject):
		return '<a href="%s" class="%s" title="%s">%s</a>' % (
			escape(str(self)), escape(self.html_link_class),
			escape(self.html_title_format % subject),
			escape(self.html_link_text)
		)

def regex_match(pattern, flags = None):
	regex = re.compile(pattern, flags)
	def match_fn(urlstring, url):
		m = regex.match(urlstring)
		if m:
			return m.group(1)
	return match_fn

def querystring_match(pattern, varname, flags = None, othervars = {}):
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
	canonical_format = "http://www.slengpung.com/v3/show_user.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?slengpung\.com/v3/show_user\.php', 'id', re.I),
	]
	html_link_class = "slengpung"
	html_link_text = "Slengpung"
	html_title_format = "%s on Slengpung"

class AmpAuthor(BaseUrl):
	canonical_format = "http://amp.dascene.net/detail.php?view=%s"
	tests = [
		querystring_match(r'https?://amp\.dascene\.net/detail\.php', 'view', re.I),
	]
	html_link_class = "amp"
	html_link_text = "AMP"
	html_title_format = "%s on Amiga Music Preservation"

class CsdbScener(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/scener/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/scener/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/csdb/scener/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"
class CsdbGroup(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/group/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/group/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/csdb/group/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"
class CsdbRelease(BaseUrl):
	canonical_format = "http://noname.c64.org/csdb/release/?id=%s"
	tests = [
		querystring_match(r'https?://noname\.c64\.org/csdb/release/', 'id', re.I),
		querystring_match(r'https?://(?:www\.)?csdb\.dk/csdb/release/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"

class NectarineArtist(BaseUrl):
	canonical_format = "http://www.scenemusic.net/demovibes/artist/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)scenemusic\.net/demovibes/artist/(\d+)', re.I),
	]
	html_link_class = "nectarine"
	html_link_text = "Nectarine"
	html_title_format = "%s on Nectarine Demoscene Radio"

class BitjamAuthor(BaseUrl):
	canonical_format = "http://www.bitfellas.org/e107_plugins/radio/radio.php?search&q=%s&type=author&page=1"
	tests = [
		querystring_match(r'https?://(?:www\.)bitfellas\.org/e107_plugins/radio/radio\.php\?search', 'q', re.I),
	]
	html_link_class = "bitjam"
	html_link_text = "BitJam"
	html_title_format = "%s on BitJam"

class ArtcityArtist(BaseUrl):
	canonical_format = "http://artcity.bitfellas.org/index.php?a=artist&id=%s"
	tests = [
		querystring_match(r'https?://artcity\.bitfellas\.org/index\.php', 'id', re.I, othervars = {'a': 'artist'}),
	]
	html_link_class = "artcity"
	html_link_text = "ArtCity"
	html_title_format = "%s on ArtCity"

class MobygamesDeveloper(BaseUrl):
	canonical_format = "http://www.mobygames.com/developer/sheet/view/developerId,%s/"
	tests = [
		regex_match(r'https?://(?:www\.)mobygames\.com/developer/sheet/view/developerId\,(\d+)', re.I),
	]
	html_link_class = "mobygames"
	html_link_text = "MobyGames"
	html_title_format = "%s on MobyGames"

class AsciiarenaArtist(BaseUrl):
	canonical_format = "http://www.asciiarena.com/info_artist.php?artist=%s&sort_by=filename"
	tests = [
		querystring_match(r'https?://(?:www\.)asciiarena\.com/info_artist\.php', 'artist', re.I),
	]
	html_link_class = "asciiarena"
	html_link_text = "AsciiArena"
	html_title_format = "%s on AsciiArena"

class ScenesatAct(BaseUrl):
	canonical_format = "http://scenesat.com/act/%s"
	tests = [
		regex_match(r'https?://(?:www\.)scenesat\.com/act/(\d+)', re.I),
	]
	html_link_class = "scenesat"
	html_link_text = "SceneSat"
	html_title_format = "%s on SceneSat Radio"

class ZxdemoAuthor(BaseUrl):
	canonical_format = "http://zxdemo.org/author.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)zxdemo\.org/author\.php', 'id', re.I),
	]
	html_link_class = "zxdemo"
	html_link_text = "ZXdemo"
	html_title_format = "%s on zxdemo.org"
class ZxdemoItem(BaseUrl):
	canonical_format = "http://zxdemo.org/item.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)zxdemo\.org/item\.php', 'id', re.I),
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

class SceneOrgFile(BaseUrl):
	tests = [
		querystring_match(r'https?://(?:www\.)scene\.org/file\.php', 'file', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)scene\.org/pub(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)scene\.org(/mirrors/.*)', re.I),
		regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*)', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*)', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*)', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*)', re.I),
		regex_match(r'http://http\.de\.scene\.org/pub(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*)', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org(/.*)', re.I),
		regex_match(r'http://http\.fr\.scene\.org(/.*)', re.I),
	]
	def __str__(self):
		return "http://www.scene.org/file.php?file=%s&fileinfo" % urllib.quote(self.param)
	html_link_class = "sceneorg"
	html_link_text = "scene.org"
	html_title_format = "%s on scene.org"

class AmigascneFile(BaseUrl):
	canonical_format = "http://ftp.amigascne.org/pub/amiga%s"
	tests = [
		regex_match(r'(?:http|ftp)://ftp\.amigascne\.org/pub/amiga(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)scene\.org/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)scene\.org/pub/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub/mirrors/amigascne(/.*)', re.I),
		regex_match(r'http://http\.de\.scene\.org/pub/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org/mirrors/amigascne(/.*)', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org/mirrors/amigascne(/.*)', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org/mirrors/amigascne(/.*)', re.I),
	]
	html_link_class = "amigascne"
	html_link_text = "amigascne.org"
	html_title_format = "%s on amigascne.org"

class DemopartyNetParty(BaseUrl):
	canonical_format = "http://www.demoparty.net/%s/"
	tests = [
		regex_match(r'https?://(?:www\.)demoparty\.net/([^/]+)', re.I),
	]
	html_link_class = "demoparty_net"
	html_link_text = "demoparty.net"
	html_title_format = "%s on demoparty.net"

class SlengpungParty(BaseUrl):
	canonical_format = "http://www.slengpung.com/?eventid=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)slengpung\.com/v3/parties\.php', 'id', re.I),
		querystring_match(r'https?://(?:www\.)slengpung.com/', 'eventid', re.I),
	]
	html_link_class = "slengpung"
	html_link_text = "Slengpung"
	html_title_format = "%s on Slengpung"

class PouetParty(BaseUrl):
	def match_pouet_party(urlstring, url):
		regex = re.compile(r'https?://(?:www\.)pouet\.net/party\.php', re.I)
		if regex.match(urlstring):
			querystring = urlparse.parse_qs(url.query)
			try:
				return "%s/%s" % (querystring['which'][0], querystring['when'][0])
			except KeyError:
				return None
	
	tests = [match_pouet_party]
	def __str__(self):
		(id,year) = self.param.split('/')
		return "http://www.pouet.net/party.php?which=%s&when=%s" % (id,year)
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
		querystring_match(r'https?://(?:www\.)?csdb\.dk/csdb/event/', 'id', re.I),
	]
	html_link_class = "csdb"
	html_link_text = "CSDb"
	html_title_format = "%s on CSDb"

class BreaksAmigaParty(BaseUrl):
	canonical_format = "http://arabuusimiehet.com/break/amiga/index.php?mode=party&partyid=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?arabuusimiehet\.com/break/amiga/index\.php', 'partyid', re.I, othervars = {'mode': 'party'}),
	]
	html_link_class = "breaks_amiga"
	html_link_text = "Break's Amiga Collection"
	html_title_format = "%s on Break's Amiga Collection"

class SceneOrgFolder(BaseUrl):
	tests = [
		querystring_match(r'https?://(?:www\.)scene\.org/dir\.php', 'dir', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)scene\.org/pub(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.(?:nl\.)scene\.org(/mirrors/.*/)$', re.I),
		regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*/)$', re.I),
		regex_match(r'http://http\.de\.scene\.org/pub(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*/)$', re.I),
		regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*/)$', re.I),
		regex_match(r'http://http\.us\.scene\.org/pub/scene.org(/.*/)$', re.I),
		regex_match(r'http://http\.fr\.scene\.org(/.*/)$', re.I),
	]
	def __str__(self):
		return "http://www.scene.org/dir.php?dir=%s" % urllib.quote(self.param)
	html_link_class = "sceneorg"
	html_link_text = "scene.org"
	html_title_format = "%s on scene.org"

class ZxdemoParty(BaseUrl):
	canonical_format = "http://zxdemo.org/party.php?id=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)zxdemo\.org/party\.php', 'id', re.I),
	]
	html_link_class = "zxdemo"
	html_link_text = "ZXdemo"
	html_title_format = "%s on zxdemo.org"

class YoutubeVideo(BaseUrl):
	canonical_format = "http://www.youtube.com/watch?v=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?youtube\.com/watch', 'v', re.I),
		regex_match(r'https?://(?:www\.)?youtube.com/embed/([^/]+)', re.I),
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

class DemosceneTvVideo(BaseUrl):
	canonical_format = "http://demoscene.tv/page.php?id=172&vsmaction=view_prod&id_prod=%s"
	tests = [
		querystring_match(r'https?://(?:www\.)?demoscene\.tv/page\.php', 'id_prod', re.I, othervars = {'id': '172', 'vsmaction': 'view_prod'}),
	]
	html_link_class = "demoscene_tv"
	html_link_text = "Demoscene.tv"
	html_title_format = "%s on Demoscene.tv"

class CappedVideo(BaseUrl):
	canonical_format = "http://capped.tv/%s"
	tests = [
		regex_match(r'https?://(?:www\.)?capped\.tv/([-_\w]+)', re.I),
	]
	html_link_class = "capped"
	html_link_text = "Capped.TV"
	html_title_format = "%s on Capped.TV"

def grok_link_by_types(urlstring, link_types):
	url = urlparse.urlparse(urlstring)
	for link_type in link_types:
		link = link_type.match(urlstring, url)
		if link:
			return link

def grok_scener_link(urlstring):
	return grok_link_by_types(urlstring, [
		TwitterAccount, SceneidAccount, SlengpungUser, AmpAuthor,
		CsdbScener, NectarineArtist, BitjamAuthor, ArtcityArtist,
		MobygamesDeveloper, AsciiarenaArtist, PouetGroup, ScenesatAct,
		ZxdemoAuthor,
		BaseUrl,
	])

def grok_group_link(urlstring):
	return grok_link_by_types(urlstring, [
		TwitterAccount, PouetGroup, ZxdemoAuthor, CsdbGroup,
		BaseUrl,
	])

def grok_production_link(urlstring):
	return grok_link_by_types(urlstring, [
		PouetProduction, CsdbRelease, ZxdemoItem, BitworldDemo,
		AmigascneFile, # must come before SceneOrgFile
		SceneOrgFile,
		YoutubeVideo, VimeoVideo, DemosceneTvVideo, CappedVideo,
		BaseUrl,
	])

def grok_party_link(urlstring):
	return grok_link_by_types(urlstring, [
		DemopartyNetParty, SlengpungParty, PouetParty, BitworldParty,
		CsdbEvent, BreaksAmigaParty, SceneOrgFolder, TwitterAccount, ZxdemoParty,
		BaseUrl,
	])
