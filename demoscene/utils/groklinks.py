# coding=utf-8
import re
import urlparse
import urllib
import urllib2
import json

from BeautifulSoup import BeautifulSoup

from django.utils.html import escape, format_html


class BaseUrl():
    def __init__(self, param):
        self.param = param

    tests = [
        lambda urlstring, url: urlstring  # always match, return full url
    ]
    canonical_format = "%s"

    @classmethod
    def extract_param(cls, urlstring, url):
        """
        Test whether 'urlstring' is a URL format that we recognise. If so, return a
        parameter (e.g. an item ID, or a file path) that captures the relevant unique
        information in this URL. If not, return None.
        """
        for test in cls.tests:
            m = test(urlstring, url)
            if m is not None:
                return m

    @classmethod
    def match(cls, urlstring, url):
        """
        Test whether 'urlstring' is a URL format that we recognise. If so, return an
        instance of this link class. If not, return None.
        """
        param = cls.extract_param(urlstring, url)
        if param is not None:
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

    def get_oembed_url(self, max_width=None, max_height=None):
        if self.oembed_base_url:
            params = {'url': str(self)}
            if self.oembed_add_format_parameter:
                params['format'] = 'json'
            if max_width:
                params['maxwidth'] = max_width
            if max_height:
                params['maxheight'] = max_height
            return "%s?%s" % (self.oembed_base_url, urllib.urlencode(params))

    supports_embed_data = False

    def get_embed_data(self):
        return None


def regex_match(pattern, flags=None, add_slash=False):
    """
    Build a function that tests a URL against the given regexp, and, if it matches,
    returns the first captured (bracketed) expression from it.
    If add_slash is true, add a trailing slash if it didn't have one already
    """
    regex = re.compile(pattern, flags)

    def match_fn(urlstring, url):
        m = regex.match(urlstring)
        if m:
            result = m.group(1)
            if add_slash and not result.endswith('/'):
                result += '/'
            return result
    return match_fn


def urldecoded_regex_match(pattern, flags=None, add_slash=False):
    """
    Build a function that tests a URL against the given regexp, and, if it matches,
    returns a URL-decoded version of the first captured (bracketed) expression from it.
    If add_slash is true, add a trailing slash if it didn't have one already
    """
    regex = re.compile(pattern, flags)

    def match_fn(urlstring, url):
        # To avoid having to deal with crazy permutations of character encodings, we require urlstring
        # to be passed a unicode string containing pure ASCII, and fail loudly if it isn't. This is
        # _probably_ a safe assumption, because strings should be arriving from (e.g.) Django forms as
        # unicode, and any non-shitty source of URLs (e.g. copy-and-paste from a browser location bar)
        # _should_ take care of URL-encoding non-ASCII characters. If that's not the case, we'll see
        # them fail and decide how to deal with them on a case-by-case basis.
        if not isinstance(urlstring, unicode):
            raise TypeError("Non-unicode string passed to urldecoded_regex_match: %r" % urlstring)
        url_bytestring = str(urlstring)  # will fail with UnicodeEncodeError if urlstring contains non-ASCII

        m = regex.match(url_bytestring)
        if m:
            unquoted_path = urllib.unquote(m.group(1))
            # unquoted_path is now a bytestring (type 'str') consisting of codepoints 0..255 in no
            # particular encoding. Decode this as iso-8859-1 to get a unicode string to go in the
            # database's 'param' field, which preserves those bytes in a way that can be restored
            # later with .encode('iso-8859-1'). (We don't care whether the bytestring is _actually_
            # supposed to be iso-8859-1.)
            result = unquoted_path.decode('iso-8859-1')
            if add_slash and not result.endswith('/'):
                result += '/'
            return result
    return match_fn


def querystring_match(pattern, varname, flags=None, othervars={}, numeric=False):
    """
    Build a function that tests a URL against the regexp 'pattern'. If it matches,
    AND all of the query parameters in 'othervars' match, return the query parameter
    named by 'varname'.
    """
    regex = re.compile(pattern, flags)

    def match_fn(urlstring, url):
        if regex.match(urlstring):
            querystring = urlparse.parse_qs(url.query)
            try:
                for (key, val) in othervars.items():
                    if querystring[key][0] != val:
                        return None

                result = querystring[varname][0]
            except KeyError:
                return None

            if numeric:
                numeric_match = re.match(r'\d+', querystring[varname][0])
                if numeric_match:
                    try:
                        result = int(numeric_match.group())
                    except ValueError:
                        return None
                else:
                    return None

            return result

    return match_fn


class TwitterAccount(BaseUrl):
    canonical_format = "https://twitter.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?twitter\.com/#!/([^/]+)', re.I),
        regex_match(r'https?://(?:www\.)?twitter\.com/([^/]+)', re.I),
    ]
    html_link_class = "twitter"
    html_link_text = "Twitter"
    html_title_format = "%s on Twitter"


class SceneidAccount(BaseUrl):
    canonical_format = "https://www.pouet.net/user.php?who=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?pouet\.net/user\.php', 'who', re.I, numeric=True),
    ]
    html_link_class = "pouet"
    html_link_text = u"Pouët"
    html_title_format = u"%s on Pouët"


class PouetGroup(BaseUrl):
    canonical_format = "https://www.pouet.net/groups.php?which=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?pouet\.net/groups\.php', 'which', re.I, numeric=True),
    ]
    html_link_class = "pouet"
    html_link_text = u"Pouët"
    html_title_format = u"%s on Pouët"


class PouetProduction(BaseUrl):
    canonical_format = "https://www.pouet.net/prod.php?which=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?pouet\.net/prod\.php', 'which', re.I, numeric=True),
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
    canonical_format = "http://csdb.dk/scener/?id=%s"
    tests = [
        querystring_match(r'https?://noname\.c64\.org/csdb/scener/(?:index\.php)?', 'id', re.I),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/scener/(?:index\.php)?', 'id', re.I),
    ]
    html_link_class = "csdb"
    html_link_text = "CSDb"
    html_title_format = "%s on CSDb"


class CsdbGroup(BaseUrl):
    canonical_format = "http://csdb.dk/group/?id=%s"
    tests = [
        querystring_match(r'https?://noname\.c64\.org/csdb/group/(?:index\.php)?', 'id', re.I),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/group/(?:index\.php)?', 'id', re.I),
    ]
    html_link_class = "csdb"
    html_link_text = "CSDb"
    html_title_format = "%s on CSDb"


class CsdbRelease(BaseUrl):
    canonical_format = "http://csdb.dk/release/?id=%s"
    tests = [
        # need to include the ? in the match so that we don't also match /release/download.php, which is totally different...
        querystring_match(r'https?://noname\.c64\.org/csdb/release/(?:index\.php)?\?', 'id', re.I),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/release/(?:index\.php)?\?', 'id', re.I),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/(?:index\.php)?\?', 'rid', re.I),
    ]
    html_link_class = "csdb"
    html_link_text = "CSDb"
    html_title_format = "%s on CSDb"


class CsdbMusic(BaseUrl):
    canonical_format = "http://csdb.dk/sid/?id=%s"
    tests = [
        # need to include the ? in the match so that we don't also match /release/download.php, which is totally different...
        querystring_match(r'https?://noname\.c64\.org/csdb/sid/(?:index\.php)?\?', 'id', re.I),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/sid/(?:index\.php)?\?', 'id', re.I),
    ]
    html_link_class = "csdb"
    html_link_text = "CSDb"
    html_title_format = "%s on CSDb"


class NectarineArtist(BaseUrl):
    canonical_format = "https://scenestream.net/demovibes/artist/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/artist/(\d+)', re.I),
        regex_match(r'https?://(?:www\.)?scenestream\.net/demovibes/artist/(\d+)', re.I),
    ]
    html_link_class = "nectarine"
    html_link_text = "Nectarine"
    html_title_format = "%s on Nectarine Demoscene Radio"


class NectarineSong(BaseUrl):
    canonical_format = "https://scenestream.net/demovibes/song/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/song/(\d+)', re.I),
        regex_match(r'https?://(?:www\.)?scenestream\.net/demovibes/song/(\d+)', re.I),
    ]
    html_link_class = "nectarine"
    html_link_text = "Nectarine"
    html_title_format = "%s on Nectarine Demoscene Radio"


class NectarineGroup(BaseUrl):
    canonical_format = "https://scenestream.net/demovibes/group/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/group/(\d+)', re.I),
        regex_match(r'https?://(?:www\.)?scenestream\.net/demovibes/group/(\d+)', re.I),
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


class ArtcityImage(BaseUrl):
    canonical_format = "http://artcity.bitfellas.org/index.php?a=show&id=%s"
    tests = [
        querystring_match(r'https?://artcity\.bitfellas\.org/index\.php', 'id', re.I, othervars={'a': 'show'}),
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
        urldecoded_regex_match(r'https?://files\.scene\.org/view(/.*)', re.I),
        urldecoded_regex_match(r'https?://files\.scene\.org/get\:\w+\-\w+(/.*)', re.I),
        urldecoded_regex_match(r'https?://files\.scene\.org/get(/.*)', re.I),
        urldecoded_regex_match(r'https?://archive\.scene\.org/pub(/.*)', re.I),
        urldecoded_regex_match(r'ftp://(?:ftp\.)?(?:nl\.)?scene\.org/pub(/.*)', re.I),
        urldecoded_regex_match(r'ftp://(?:ftp\.)?(?:nl\.)?scene\.org(/mirrors/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*)', re.I),
        urldecoded_regex_match(r'https?://ftp\.scene\.org/pub(/.*)', re.I),
        urldecoded_regex_match(r'https?://http\.no\.scene\.org/scene\.org(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*)', re.I),
        urldecoded_regex_match(r'http://(?:http\.)?de\.scene\.org/pub(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*)', re.I),
        urldecoded_regex_match(r'https?://http\.us\.scene\.org/pub/scene.org(/.*)', re.I),
        urldecoded_regex_match(r'http://http\.fr\.scene\.org(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.hu\.scene\.org/mirrors/scene.org(/.*)', re.I),
        urldecoded_regex_match(r'https?://http\.hu\.scene\.org(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.pl\.scene\.org/pub/demos(/.*)', re.I),
        urldecoded_regex_match(r'https?://http\.pl\.scene\.org/pub/demos(/.*)', re.I),
        urldecoded_regex_match(r'ftp://ftp\.ua\.scene\.org/pub/mirrors/sceneorg(/.*)', re.I),
    ]

    @property
    def info_url(self):
        return u"https://files.scene.org/view%s" % urllib.quote(self.param.encode('iso-8859-1'))

    @property
    def auto_mirror_url(self):
        return u"https://files.scene.org/get%s" % urllib.quote(self.param.encode('iso-8859-1'))

    def __unicode__(self):
        return self.info_url

    html_link_class = "sceneorg"
    html_link_text = "scene.org"
    html_title_format = "%s on scene.org"

    @property
    def nl_url(self):
        return u"ftp://ftp.scene.org/pub%s" % urllib.quote(self.param.encode('iso-8859-1'))

    @property
    def nl_http_url(self):
        return u"http://archive.scene.org/pub%s" % urllib.quote(self.param.encode('iso-8859-1'))

    @property
    def nl_https_url(self):
        return u"https://archive.scene.org/pub%s" % urllib.quote(self.param.encode('iso-8859-1'))

    @property
    def download_url(self):
        return self.nl_url

    def as_download_link(self):
        return '''
            <div><a href="%s" class="primary">Download (scene.org)</a> - <a href="%s" class="secondary">file info</a></div>
        ''' % (
            escape(self.auto_mirror_url), escape(self.info_url)
        )


class AmigascneFile(BaseUrl):
    canonical_format = "ftp://ftp.amigascne.org/pub/amiga%s"
    tests = [
        regex_match(r'(?:http|ftp)://(?:\w+\@)?(?:ftp\.)?amigascne\.org/pub/amiga(/.*)', re.I),
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
            '<li><a class="country country_nl" href="%s">nl</a></li>' % escape(self.nl_url),
            '<li><a href="%s" class="country country_us">us</a></li>' % escape(self.us_http_url),
        ]

        return links

    @property
    def nl_url(self):
        return "ftp://ftp.scene.org/pub/mirrors/amigascne%s" % self.param

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
            '<li><a class="country country_nl" href="%s">nl</a></li>' % escape(self.nl_url),
            '<li><a href="%s" class="country country_us">us</a></li>' % escape(self.us_http_url),
        ]

        return links

    @property
    def nl_url(self):
        return "ftp://ftp.scene.org/pub/mirrors/padua%s" % self.param

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
        regex_match(r'(?:ftp|http)://(?:ftp\.)?modland\.com(/.*)', re.I),
        regex_match(r'ftp://modland\.ziphoid\.com(/.*)', re.I),
        regex_match(r'ftp://hangar18\.exotica\.org\.uk/modland(/.*)', re.I),
        regex_match(r'ftp://aero.exotica.org.uk/pub/mirrors/modland(/.*)', re.I),
        regex_match(r'(?:ftp|http)://modland\.ziphoid\.com(/.*)', re.I),
        regex_match(r'ftp://ftp\.amigascne\.org/mirrors/ftp\.modland\.com(/.*)', re.I),
        regex_match(r'ftp://ftp\.rave\.ca(/.*)', re.I),
        regex_match(r'ftp://modland\.mindkiller\.com/modland(/.*)', re.I),
        regex_match(r'http://modland\.antarctica\.no(/.*)', re.I),
        exotica_querystring_match(),
    ]
    html_link_class = "modland"
    html_link_text = "Modland"
    html_title_format = "%s on Modland"

    @property
    def mirror_links(self):
        links = [
            '<li><a class="country country_uk" href="%s">uk</a></li>' % escape(self.uk_url),
            '<li><a href="%s" class="country country_se">se</a></li>' % escape(self.se_url),
            '<li><a href="%s" class="country country_us">us</a></li>' % escape(self.us_url),
            '<li><a href="%s" class="country country_ca">ca</a></li>' % escape(self.ca_url),
            '<li><a href="%s" class="country country_no">no</a></li>' % escape(self.no_url),
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
    
    @property
    def no_url(self):
        return "http://modland.antarctica.no%s" % self.param

    def as_download_link(self):
        mirrors_html = ' '.join(self.mirror_links)
        return '''
            <div class="primary"><a href="%s">Download from Modland</a></div>
            <div class="secondary">mirrors: <ul class="download_mirrors">%s</ul></div>
        ''' % (
            escape(str(self)), mirrors_html
        )


class FujiologyFile(BaseUrl):
    canonical_format = "ftp://fujiology.untergrund.net/users/ltk_tscc/fujiology%s"
    tests = [
        regex_match(r'ftp://(?:fujiology\.|ftp\.)untergrund\.net/users/ltk_tscc/fujiology(/.*)', re.I),
    ]
    html_link_class = "fujiology"
    html_link_text = "Fujiology"
    html_title_format = "%s on the Fujiology Archive"


class FujiologyFolder(BaseUrl):
    canonical_format = "ftp://fujiology.untergrund.net/users/ltk_tscc/fujiology%s"
    tests = [
        regex_match(r'ftp://(?:fujiology\.|ftp\.)?untergrund\.net/users/ltk_tscc/fujiology(/.*)', re.I, add_slash=True),
    ]
    html_link_class = "fujiology"
    html_link_text = "Fujiology"
    html_title_format = "%s on the Fujiology Archive"


class UntergrundFile(BaseUrl):
    canonical_format = "ftp://ftp.untergrund.net%s"
    tests = [
        regex_match(r'ftp://(?:ftp\.)?untergrund\.net(/.*)', re.I),
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


class CsdbEvent(BaseUrl):
    canonical_format = "http://csdb.dk/event/?id=%s"
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
        urldecoded_regex_match(r'https?://files\.scene\.org/browse(/.*)', re.I, add_slash=True),
        querystring_match(r'https?://(?:www\.)?scene\.org/dir\.php', 'dir', re.I),
        urldecoded_regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org(/mirrors/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'http://(?:http\.)?de\.scene\.org/pub(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'http://http\.us\.scene\.org/pub/scene.org(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'http://http\.fr\.scene\.org(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.pl\.scene\.org/pub/demos(/.*)', re.I, add_slash=True),
        urldecoded_regex_match(r'http://http\.pl\.scene\.org/pub/demos(/.*)', re.I, add_slash=True),
    ]

    def __unicode__(self):
        return u"https://files.scene.org/browse%s" % urllib.quote(self.param.encode('iso-8859-1'))
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
    def match_long_url(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?youtube\.com/watch\?', re.I)
        if regex.match(urlstring):
            querystring = urlparse.parse_qs(url.query)
            try:
                if 't' in querystring:
                    return "%s/%s" % (querystring['v'][0], querystring['t'][0])
                else:
                    return querystring['v'][0]
            except KeyError:
                return None

    def match_embed_url(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?youtube\.com/embed/([\w\-\_]+)', re.I)
        m = regex.match(urlstring)
        if m:
            v = m.group(1)
            querystring = urlparse.parse_qs(url.query)
            if 'start' in querystring:
                return "%s/%s" % (v, querystring['start'][0])
            else:
                return v

    def match_short_url(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?youtu\.be/([\w\-\_]+)', re.I)
        m = regex.match(urlstring)
        if m:
            v = m.group(1)
            querystring = urlparse.parse_qs(url.query)
            if 't' in querystring:
                return "%s/%s" % (v, querystring['t'][0])
            else:
                return v

    tests = [
        match_long_url,
        match_embed_url,
        match_short_url,
    ]
    html_link_class = "youtube"
    html_link_text = "YouTube"
    html_title_format = "%s on YouTube"
    is_streaming_video = True

    oembed_base_url = "https://www.youtube.com/oembed"
    oembed_add_format_parameter = True

    supports_embed_data = True

    def __unicode__(self):
        if '/' in self.param:
            (id, timestamp) = self.param.split('/')
            return u"https://www.youtube.com/watch?v=%s&t=%s" % (id, timestamp)
        else:
            return u"https://www.youtube.com/watch?v=%s" % self.param

    def get_embed_data(self, oembed_only=False):
        embed_data = {}

        if not oembed_only:
            url = str(self)
            response = urllib2.urlopen(url)
            response_data = response.read()
            response.close()
            soup = BeautifulSoup(response_data)
            embed_data['video_width'] = int(soup.find('meta', {'property': 'og:video:width'})['content'])
            embed_data['video_height'] = int(soup.find('meta', {'property': 'og:video:height'})['content'])

        oembed_thumbnail_url = self.get_oembed_url(max_width=400, max_height=300)
        response = urllib2.urlopen(oembed_thumbnail_url)
        response_data = response.read()
        response.close()
        oembed_data = json.loads(response_data)
        embed_data['thumbnail_url'] = oembed_data['thumbnail_url']
        embed_data['thumbnail_width'] = oembed_data['thumbnail_width']
        embed_data['thumbnail_height'] = oembed_data['thumbnail_height']

        return embed_data

    def get_embed_html(self, width, height, autoplay=True):
        if '/' in self.param:
            (id, timestamp) = self.param.split('/')

            # timestamps given in the format 1m30s need to be converted to just seconds,
            # because fuck you that's why
            m = re.match(r'(\d+)m(\d+)', timestamp)
            if m:
                (minutes, seconds) = m.groups()
                timestamp = int(minutes) * 60 + int(seconds)

            embed_url = "https://www.youtube.com/embed/%s?start=%s" % (id, timestamp)
            if autoplay:
                embed_url += "&autoplay=1"
        else:
            embed_url = "https://www.youtube.com/embed/%s" % self.param
            if autoplay:
                embed_url += "?autoplay=1"
        return format_html(
            """<iframe width="{}" height="{}" src="{}" frameborder="0" allowfullscreen></iframe>""",
            width, height, embed_url
        )


class YoutubeUser(BaseUrl):
    canonical_format = "https://www.youtube.com/user/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?youtube\.com/user/([^\/\?]+)', re.I),
    ]
    html_link_class = "youtube"
    html_link_text = "YouTube"
    html_title_format = "%s on YouTube"


class YoutubeChannel(BaseUrl):
    canonical_format = "https://www.youtube.com/channel/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?youtube\.com/channel/([^\/\?]+)', re.I),
    ]
    html_link_class = "youtube"
    html_link_text = "YouTube"
    html_title_format = "%s on YouTube"


class VimeoVideo(BaseUrl):
    canonical_format = "https://vimeo.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?vimeo\.com/(\d+)', re.I),
    ]
    html_link_class = "vimeo"
    html_link_text = "Vimeo"
    html_title_format = "%s on Vimeo"
    is_streaming_video = True

    oembed_base_url = "https://vimeo.com/api/oembed.json"
    oembed_add_format_parameter = False

    supports_embed_data = True

    def get_embed_data(self):
        embed_data = {}

        oembed_thumbnail_url = self.get_oembed_url(max_width=400, max_height=300)
        response = urllib2.urlopen(oembed_thumbnail_url)
        response_data = response.read()
        response.close()
        oembed_data = json.loads(response_data)
        embed_data['thumbnail_url'] = oembed_data['thumbnail_url']
        embed_data['thumbnail_width'] = oembed_data['thumbnail_width']
        embed_data['thumbnail_height'] = oembed_data['thumbnail_height']

        oembed_url = self.get_oembed_url()
        response = urllib2.urlopen(oembed_url)
        response_data = response.read()
        response.close()
        oembed_data = json.loads(response_data)
        embed_data['video_width'] = oembed_data['width']
        embed_data['video_height'] = oembed_data['height']

        return embed_data

    def get_embed_html(self, width, height, autoplay=True):
        embed_url = "https://player.vimeo.com/video/%s" % self.param
        if autoplay:
            embed_url += "?autoplay=1"
        return format_html(
            """<iframe width="{}" height="{}" src="{}" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>""",
            width, height, embed_url
        )


class VimeoUser(BaseUrl):
    canonical_format = "https://vimeo.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?vimeo\.com/([\w-]+)/?$', re.I),
    ]
    html_link_class = "vimeo"
    html_link_text = "Vimeo"
    html_title_format = "%s on Vimeo"


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
        querystring_match(r'https?://(?:www\.)?capped\.tv/playeralt\.php', 'vid', re.I),
        regex_match(r'https?://(?:www\.)?capped\.tv/([-_\w]+)$', re.I),
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
    canonical_format = "https://www.facebook.com/%s"
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
    canonical_format = "https://soundcloud.com/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?soundcloud\.com/([^\/]+)', re.I),
    ]
    html_link_class = "soundcloud"
    html_link_text = "SoundCloud"
    html_title_format = "%s on SoundCloud"


class HearthisUser(BaseUrl):
    canonical_format = "https://hearthis.at/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?hearthis\.at/([^\/]+)', re.I),
    ]
    html_link_class = "hearthis"
    html_link_text = "hearthis.at"
    html_title_format = "%s on hearthis.at"


class SoundcloudTrack(BaseUrl):
    canonical_format = "https://soundcloud.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?soundcloud\.com/([^\/]+/[^\/]+)', re.I),
    ]
    html_link_class = "soundcloud"
    html_link_text = "SoundCloud"
    html_title_format = "%s on SoundCloud"


class HearthisTrack(BaseUrl):
    canonical_format = "https://hearthis.at/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?hearthis\.at/([^\/]+/[^\/]+)', re.I),
    ]
    html_link_class = "hearthis"
    html_link_text = "hearthis.at"
    html_title_format = "%s on hearthis.at"


class DiscogsEntry(BaseUrl):  # for use as an abstract superclass
    html_link_class = "discogs"
    html_link_text = "Discogs"
    html_title_format = "%s on Discogs"


class DiscogsArtist(DiscogsEntry):
    canonical_format = "https://www.discogs.com/artist/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?discogs\.com/artist/(.+)', re.I),
    ]


class DiscogsLabel(DiscogsEntry):
    canonical_format = "https://www.discogs.com/label/%s"
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
    canonical_format = "https://modarchive.org/member.php?%s"
    tests = [
        regex_match(r'https?://(?:www\.)?modarchive\.org/member\.php\?(\d+)', re.I),
        querystring_match(r'https?://(?:www\.)?modarchive\.org/index\.php', 'query', re.I, othervars={'request': 'view_profile'}),
    ]
    html_link_class = "modarchive"
    html_link_text = "ModArchive"
    html_title_format = "%s on The Mod Archive"


class ModarchiveModule(BaseUrl):
    canonical_format = "https://modarchive.org/module.php?%s"
    tests = [
        regex_match(r'https?://(?:www\.|lite\.)?modarchive\.org/module\.php\?(\d+)', re.I),
        querystring_match(r'https?://(?:www\.|lite\.)?modarchive\.org/index\.php', 'query', re.I, othervars={'request': 'view_by_moduleid'}),
        querystring_match(r'https?://(?:www\.|lite\.)?modarchive\.org/data/downloads\.php', 'moduleid', re.I),
        querystring_match(r'https?://api.modarchive\.org/downloads\.php', 'moduleid', re.I),
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


class ZxArtAuthor(ZxArtEntry):
    canonical_format = "http://zxart.ee/eng/authors/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/authors/(\w/[^\/]+)(/qid:\d+)?/?', re.I),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/avtory/(\w/[^\/]+)(/qid:\d+)?/?', re.I),
    ]


class ZxArtPicture(ZxArtEntry):
    canonical_format = "http://zxart.ee/eng/graphics/authors/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/authors/([^\/]+/[^\/]+/[^\/]+)/?', re.I),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/avtory/([^\/]+/[^\/]+/[^\/]+)/?', re.I),
    ]


class ZxArtMusic(ZxArtEntry):
    canonical_format = "http://zxart.ee/eng/music/authors/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/authors/([^\/]+/[^\/]+/[^\/]+)/?', re.I),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/avtory/([^\/]+/[^\/]+/[^\/]+)/?', re.I),
    ]


class ZxArtPartyGraphics(ZxArtEntry):
    canonical_format = "http://zxart.ee/eng/graphics/parties/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/parties/([^\/]+/[^\/]+)/?', re.I),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/pati/([^\/]+/[^\/]+)/?', re.I),
    ]


class ZxArtPartyMusic(ZxArtEntry):
    canonical_format = "http://zxart.ee/eng/music/parties/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/parties/([^\/]+/[^\/]+)/?', re.I),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/pati/([^\/]+/[^\/]+)/?', re.I),
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
    canonical_format = "https://play.spotify.com/artist/%s"
    tests = [
        regex_match(r'https?://(?:open|play)\.spotify\.com/artist/(\w+)', re.I),
    ]
    html_link_class = "spotify"
    html_link_text = "Spotify"
    html_title_format = "%s on Spotify"


class SpotifyTrack(BaseUrl):
    canonical_format = "https://play.spotify.com/track/%s"
    tests = [
        regex_match(r'https?://(?:open|play)\.spotify\.com/track/(\w+)', re.I),
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


class GithubDirectory(BaseUrl):
    def __unicode__(self):
        params = self.param.split('/')
        user, repo = params[0:2]
        dirs = '/'.join(params[2:])
        return u"http://github.com/%s/%s/tree/%s" % (user, repo, dirs)

    regex = re.compile(r'https?://github\.com/([^\/]+)/([^\/]+)/tree/(.+)$', re.I)

    def github_dir_match(urlstring, url):
        m = GithubDirectory.regex.match(urlstring)
        if m:
            return "%s/%s/%s" % (m.group(1), m.group(2), m.group(3))

    tests = [
        github_dir_match,
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


class StonishDisk(BaseUrl):
    canonical_format = "http://stonish.net/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?stonish\.net/([\w\-]+\#st\d+)', re.I),
    ]
    html_link_class = "stonish"
    html_link_text = "Stonish"
    html_title_format = "%s on Stonish"


class ZxTunesArtist(BaseUrl):
    canonical_format = "http://zxtunes.com/author.php?id=%s&ln=eng"
    tests = [
        querystring_match(r'http://(?:www\.)?zxtunes\.com/author\.php', 'id', re.I),
    ]
    html_link_class = "zxtunes"
    html_link_text = "ZXTunes"
    html_title_format = "%s on ZXTunes"


class GameboyDemospottingAuthor(BaseUrl):
    canonical_format = "http://gameboy.modermodemet.se/en/author/%s"
    tests = [
        regex_match(r'https?://gameboy\.modermodemet\.se/\w+/author/(\d+)', re.I),
    ]
    html_link_class = "gameboydemospotting"
    html_link_text = "Gameboy Demospotting"
    html_title_format = "%s on Gameboy Demospotting"


class GameboyDemospottingDemo(BaseUrl):
    canonical_format = "http://gameboy.modermodemet.se/en/demo/%s"
    tests = [
        regex_match(r'https?://gameboy\.modermodemet\.se/\w+/demo/(\d+)', re.I),
    ]
    html_link_class = "gameboydemospotting"
    html_link_text = "Gameboy Demospotting"
    html_title_format = "%s on Gameboy Demospotting"


class PixeljointArtist(BaseUrl):
    canonical_format = "http://pixeljoint.com/p/%s.htm"
    tests = [
        regex_match(r'https?://(?:www\.)?pixeljoint\.com/p/(\d+)\.htm', re.I),
    ]
    html_link_class = "pixeljoint"
    html_link_text = "Pixeljoint"
    html_title_format = "%s on Pixeljoint"


class PixeljointImage(BaseUrl):
    canonical_format = "http://pixeljoint.com/pixelart/%s.htm"
    tests = [
        regex_match(r'https?://(?:www\.)?pixeljoint\.com/pixelart/(\d+)\.htm', re.I),
    ]
    html_link_class = "pixeljoint"
    html_link_text = "Pixeljoint"
    html_title_format = "%s on Pixeljoint"


class Plus4WorldProduction(BaseUrl):
    canonical_format = "http://plus4world.powweb.com/software/%s"
    tests = [
        regex_match(r'https?://plus4world\.powweb\.com/software/(\w+)', re.I),
    ]
    html_link_class = "plus4world"
    html_link_text = "Plus/4 World"
    html_title_format = "%s on Plus/4 World"


class Plus4WorldGroup(BaseUrl):
    canonical_format = "http://plus4world.powweb.com/groups/%s"
    tests = [
        regex_match(r'https?://plus4world\.powweb\.com/groups/(\w+)', re.I),
    ]
    html_link_class = "plus4world"
    html_link_text = "Plus/4 World"
    html_title_format = "%s on Plus/4 World"


class Plus4WorldMember(BaseUrl):
    canonical_format = "http://plus4world.powweb.com/members/%s"
    tests = [
        regex_match(r'https?://plus4world\.powweb\.com/members/(\w+)', re.I),
    ]
    html_link_class = "plus4world"
    html_link_text = "Plus/4 World"
    html_title_format = "%s on Plus/4 World"


class BandcampEntry(BaseUrl):  # Bandcamp abstract superclass
    html_link_class = "bandcamp"
    html_link_text = "Bandcamp"
    html_title_format = "%s on Bandcamp"


class BandcampArtist(BandcampEntry):
    canonical_format = "https://%s.bandcamp.com/"
    tests = [
        regex_match(r'https?://([\w-]+)\.bandcamp\.com/?$', re.I),
    ]


class BandcampTrack(BandcampEntry):
    def match_bandcamp_release(urlstring, url):
        regex = re.compile(r'https?://([\w-]+)\.bandcamp\.com/track/([\w-]+)', re.I)
        match = regex.match(urlstring)
        if match:
            domain, name = match.groups()
            return "%s/%s" % (domain, name)

    tests = [match_bandcamp_release]

    def __unicode__(self):
        (domain, name) = self.param.split('/')
        return u"https://%s.bandcamp.com/track/%s" % (domain, name)


RELEASER_LINK_TYPES = [
    TwitterAccount, SceneidAccount, SlengpungUser, AmpAuthor,
    CsdbScener, CsdbGroup, NectarineArtist, NectarineGroup, BitjamAuthor, ArtcityArtist,
    MobygamesDeveloper, AsciiarenaArtist, AsciiarenaCrew, PouetGroup,
    ScenesatAct, ZxdemoAuthor, FacebookPage,
    PushnpopGroup, PushnpopProfile, SceneOrgFolder, FujiologyFolder,
    GooglePlusPage, SoundcloudUser, HearthisUser, YoutubeUser, YoutubeChannel,
    DeviantartUser, ModarchiveMember, WikipediaPage,
    SpeccyWikiPage, DiscogsArtist, DiscogsLabel,
    HallOfLightArtist, SpotifyArtist, KestraBitworldAuthor,
    GithubAccount, GithubRepo, AtarimaniaPage, GameboyDemospottingAuthor, PixeljointArtist,
    ZxArtAuthor, ZxTunesArtist, InternetArchivePage,
    Plus4WorldGroup, Plus4WorldMember, BandcampArtist, VimeoUser,
    WaybackMachinePage, BaseUrl,
]

PRODUCTION_LINK_TYPES = [
    PouetProduction, CsdbRelease, ZxdemoItem,
    YoutubeVideo, VimeoVideo, DemosceneTvVideo, CappedVideo, DhsVideoDbVideo,
    AsciiarenaRelease, KestraBitworldRelease, StonishDisk, ArtcityImage,
    ScenesatTrack, ModlandFile, SoundcloudTrack, HearthisTrack, BandcampTrack, CsdbMusic, NectarineSong,
    ModarchiveModule, BitjamSong, PushnpopProduction, SpotifyTrack, Plus4WorldProduction,
    AmigascneFile, PaduaOrgFile,  # sites mirrored by scene.org - must come before SceneOrgFile
    SceneOrgFile, FujiologyFile, UntergrundFile, GithubAccount, GithubRepo, GithubDirectory,
    WikipediaPage, SpeccyWikiPage, AtarimaniaPage, HallOfLightGame, PixeljointImage,
    DiscogsRelease, ZxArtPicture, ZxArtMusic, InternetArchivePage, GameboyDemospottingDemo,
    WaybackMachinePage, BaseUrl,
]

EMBEDDABLE_PRODUCTION_LINK_TYPES = [pl for pl in PRODUCTION_LINK_TYPES if hasattr(pl, 'oembed_base_url')]

PRODUCTION_DOWNLOAD_LINK_TYPES = [
    'AmigascneFile', 'SceneOrgFile', 'FujiologyFile', 'UntergrundFile', 'PaduaOrgFile', 'ModlandFile'
]

PRODUCTION_EXTERNAL_LINK_TYPES = [
    'PouetProduction', 'CsdbRelease', 'CsdbMusic', 'ZxdemoItem', 'YoutubeVideo',
    'VimeoVideo', 'DemosceneTvVideo', 'CappedVideo', 'DhsVideoDbVideo', 'AsciiarenaRelease', 'ScenesatTrack',
    'ModarchiveModule', 'BitjamSong', 'SoundcloudTrack', 'HearthisTrack', 'NectarineSong', 'KestraBitworldRelease',
    'PushnpopProduction', 'WikipediaPage', 'SpeccyWikiPage', 'SpotifyTrack', 'BandcampTrack', 'StonishDisk',
    'GithubAccount', 'GithubRepo', 'GithubDirectory', 'AtarimaniaPage', 'HallOfLightGame', 'DiscogsRelease',
    'ZxArtPicture', 'ZxArtMusic', 'InternetArchivePage', 'GameboyDemospottingDemo',
    'PixeljointImage', 'ArtcityImage', 'Plus4WorldProduction',
]

PARTY_LINK_TYPES = [
    DemopartyNetParty, SlengpungParty, PouetParty,
    CsdbEvent, BreaksAmigaParty, SceneOrgFolder, FujiologyFolder, TwitterAccount, ZxdemoParty,
    PushnpopParty, KestraBitworldParty, YoutubeUser, YoutubeChannel,
    FacebookPage, GooglePlusPage, GooglePlusEvent, LanyrdEvent, WikipediaPage,
    SpeccyWikiPage, ZxArtPartyGraphics, ZxArtPartyMusic, WaybackMachinePage, BaseUrl,
]

# Links that should be kept for archiving purposes, but not shown or available for editing
ARCHIVED_LINK_TYPES = [
    'ZxdemoAuthor', 'ZxdemoItem', 'ZxdemoParty',
    'PushnpopProduction', 'PushnpopParty', 'PushnpopGroup', 'PushnpopProfile',
    'DemosceneTvVideo',
    'LanyrdEvent',
    'GooglePlusPage', 'GooglePlusEvent',
    'CappedVideo',
    'AsciiarenaArtist', 'AsciiarenaCrew', 'AsciiarenaRelease',
]


def grok_link_by_types(urlstring, link_types):
    """
    Try to turn urlstring into a link object by matching it against each of the link types in
    the link_type list. If none of them match, return None.
    """
    url = urlparse.urlparse(urlstring)
    for link_type in link_types:
        link = link_type.match(urlstring, url)
        if link:
            return link
