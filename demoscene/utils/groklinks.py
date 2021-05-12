# coding=utf-8
from __future__ import absolute_import, unicode_literals

import json
import re
import urllib

from bs4 import BeautifulSoup
from django.utils.html import escape, format_html


class Site:
    def __init__(
        self, name, long_name=None, classname=None, title_format=None, url=None,
        allowed_schemes=None, allowed_hostnames=None
    ):
        self.name = name
        self.long_name = long_name or name
        self.classname = classname or name.lower()
        self.title_format = title_format or ("%%s on %s" % self.long_name)

        if url:
            parsed_url = urllib.parse.urlparse(url)

        # which URL schemes are allowed for this site?
        # Use the explicitly passed list if there is one
        # (or leave it as None if a 'url' param wasn't passed either)
        if allowed_schemes is not None or url is None:
            self.allowed_schemes = allowed_schemes
        elif parsed_url.scheme in ('http', 'https'):
            # if URL is specified as http OR https, recognise both
            self.allowed_schemes = ['http', 'https']
        else:
            self.allowed_schemes = [parsed_url.scheme]

        # which hostnames are recognised for this site?
        # Use the explicitly passed list if there is one
        # (or leave it as None if a 'url' param wasn't passed either)
        if allowed_hostnames is not None or url is None:
            self.allowed_hostnames = allowed_hostnames
        else:
            # if allowed_schemes indicates that this is a website
            # (and not ftp or something else weird), allow both
            is_website = self.allowed_schemes is not None and (
                'http' in self.allowed_schemes
                or 'https' in self.allowed_schemes
            )
            if is_website and parsed_url.hostname.startswith('www.'):
                self.allowed_hostnames = [
                    parsed_url.hostname,
                    parsed_url.hostname.replace('www.', '', 1)
                ]
            elif is_website:
                self.allowed_hostnames = [
                    parsed_url.hostname, 'www.' + parsed_url.hostname
                ]
            else:
                self.allowed_hostnames = [parsed_url.hostname]

    def matches_url(self, url):
        return (
            (self.allowed_schemes is None or url.scheme in self.allowed_schemes)
            and (self.allowed_hostnames is None or url.hostname in self.allowed_hostnames)
        )

    def get_link_html(self, url, subject):
        return format_html(
            '<a href="{url}" class="{classname}" title="{title}">{label}</a>',
            url=url,
            classname=self.classname,
            title=(self.title_format % subject),
            label=self.name,
        )


class AbstractBaseUrl():
    def __init__(self, param):
        self.param = param

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
        if not cls.site.matches_url(url):
            return None

        param = cls.extract_param(urlstring, url)
        if param is not None:
            return cls(param)

    def __str__(self):
        return self.canonical_format % self.param

    def as_html(self, subject):
        return self.site.get_link_html(str(self), subject)

    @property
    def download_link_label(self):
        return urllib.parse.urlparse(str(self)).hostname

    @property
    def html_link_class(self):
        return self.site.classname

    def as_download_link(self):
        return '<div class="primary"><a href="%s">Download (%s)</a></div>' % (
            escape(str(self)), escape(self.download_link_label)
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
            return "%s?%s" % (self.oembed_base_url, urllib.parse.urlencode(params))

    supports_embed_data = False

    def get_embed_data(self):
        return None


class BaseUrl(AbstractBaseUrl):  # catch-all handler where nothing more specific is found
    site = Site("WWW", classname="website", title_format="%s website")

    tests = [
        lambda urlstring, url: urlstring  # always match, return full url
    ]
    canonical_format = "%s"


def regex_match(pattern, flags=re.IGNORECASE, add_slash=False):
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


def urldecoded_regex_match(pattern, flags=re.IGNORECASE, add_slash=False):
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
        if not isinstance(urlstring, str):  # pragma: no cover
            # on py3, non-unicode strings will fail regexp matches anyhow, so don't expect to reach this
            raise TypeError("Non-unicode string passed to urldecoded_regex_match: %r" % urlstring)
        urlstring.encode('ascii')  # will fail with UnicodeEncodeError if urlstring contains non-ASCII

        m = regex.match(urlstring)
        if m:
            unquoted_path = urllib.parse.unquote_to_bytes(m.group(1))
            # unquoted_path is now a bytestring consisting of codepoints 0..255 in no
            # particular encoding. Decode this as iso-8859-1 to get a unicode string to go in the
            # database's 'param' field, which preserves those bytes in a way that can be restored
            # later with .encode('iso-8859-1'). (We don't care whether the bytestring is _actually_
            # supposed to be iso-8859-1.)
            result = unquoted_path.decode('iso-8859-1')
            if add_slash and not result.endswith('/'):
                result += '/'
            return result
    return match_fn


def querystring_match(pattern, varname, flags=re.IGNORECASE, othervars={}, numeric=False):
    """
    Build a function that tests a URL against the regexp 'pattern'. If it matches,
    AND all of the query parameters in 'othervars' match, return the query parameter
    named by 'varname'.
    """
    regex = re.compile(pattern, flags)

    def match_fn(urlstring, url):
        if regex.match(urlstring):
            querystring = urllib.parse.parse_qs(url.query)
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
                    result = int(numeric_match.group())
                else:
                    return None

            return result

    return match_fn


class TwitterAccount(AbstractBaseUrl):
    site = Site("Twitter", url='https://twitter.com/')
    canonical_format = "https://twitter.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?twitter\.com/#!/([^/]+)'),
        regex_match(r'https?://(?:www\.)?twitter\.com/([^/]+)'),
    ]


pouet = Site(u"Pouët", classname="pouet", url='https://www.pouet.net/')


class SceneidAccount(AbstractBaseUrl):
    site = pouet
    canonical_format = "https://www.pouet.net/user.php?who=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?pouet\.net/user\.php', 'who', numeric=True),
    ]


class PouetGroup(AbstractBaseUrl):
    site = pouet
    canonical_format = "https://www.pouet.net/groups.php?which=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?pouet\.net/groups\.php', 'which', numeric=True),
    ]


class PouetProduction(AbstractBaseUrl):
    site = pouet
    canonical_format = "https://www.pouet.net/prod.php?which=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?pouet\.net/prod\.php', 'which', numeric=True),
    ]


slengpung = Site("Slengpung", url='http://www.slengpung.com/')


class SlengpungUser(AbstractBaseUrl):
    site = slengpung
    canonical_format = "http://www.slengpung.com/?userid=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?slengpung\.com/v[\d_]+/show_user\.php', 'id'),
        querystring_match(r'https?://(?:www\.)?slengpung\.com/', 'userid'),
    ]


class AmpAuthor(AbstractBaseUrl):
    site = Site("AMP", long_name="Amiga Music Preservation", url='https://amp.dascene.net/')
    canonical_format = "https://amp.dascene.net/detail.php?view=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?amp\.dascene\.net/detail\.php', 'view'),
    ]


csdb = Site(
    "CSDb", url='https://csdb.dk/', allowed_hostnames=['csdb.dk', 'www.csdb.dk', 'noname.c64.org']
)


class CsdbScener(AbstractBaseUrl):
    site = csdb
    canonical_format = "https://csdb.dk/scener/?id=%s"
    tests = [
        querystring_match(r'https?://noname\.c64\.org/csdb/scener/(?:index\.php)?', 'id'),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/scener/(?:index\.php)?', 'id'),
    ]


class CsdbGroup(AbstractBaseUrl):
    site = csdb
    canonical_format = "https://csdb.dk/group/?id=%s"
    tests = [
        querystring_match(r'https?://noname\.c64\.org/csdb/group/(?:index\.php)?', 'id'),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/group/(?:index\.php)?', 'id'),
    ]


class CsdbRelease(AbstractBaseUrl):
    site = csdb
    canonical_format = "https://csdb.dk/release/?id=%s"
    tests = [
        # need to include the ? in the match so that we don't also match /release/download.php,
        # which is totally different...
        querystring_match(r'https?://noname\.c64\.org/csdb/release/(?:index\.php)?\?', 'id'),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/release/(?:index\.php)?\?', 'id'),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/(?:index\.php)?\?', 'rid'),
    ]


class CsdbMusic(AbstractBaseUrl):
    site = csdb
    canonical_format = "https://csdb.dk/sid/?id=%s"
    tests = [
        # need to include the ? in the match so that we don't also match /release/download.php,
        # which is totally different...
        querystring_match(r'https?://noname\.c64\.org/csdb/sid/(?:index\.php)?\?', 'id'),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/sid/(?:index\.php)?\?', 'id'),
    ]


nectarine = Site(
    "Nectarine", long_name="Nectarine Demoscene Radio", url='https://scenestream.net/',
    allowed_hostnames=['scenemusic.net', 'www.scenemusic.net', 'scenestream.net', 'www.scenestream.net']
)


class NectarineArtist(AbstractBaseUrl):
    site = nectarine
    canonical_format = "https://scenestream.net/demovibes/artist/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/artist/(\d+)'),
        regex_match(r'https?://(?:www\.)?scenestream\.net/demovibes/artist/(\d+)'),
    ]


class NectarineSong(AbstractBaseUrl):
    site = nectarine
    canonical_format = "https://scenestream.net/demovibes/song/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/song/(\d+)'),
        regex_match(r'https?://(?:www\.)?scenestream\.net/demovibes/song/(\d+)'),
    ]


class NectarineGroup(AbstractBaseUrl):
    site = nectarine
    canonical_format = "https://scenestream.net/demovibes/group/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?scenemusic\.net/demovibes/group/(\d+)'),
        regex_match(r'https?://(?:www\.)?scenestream\.net/demovibes/group/(\d+)'),
    ]


bitjam = Site("BitJam", url='http://www.bitfellas.org/')


class BitjamAuthor(AbstractBaseUrl):
    site = bitjam
    canonical_format = "http://www.bitfellas.org/e107_plugins/radio/radio.php?search&q=%s&type=author&page=1"
    tests = [
        querystring_match(r'https?://(?:www\.)?bitfellas\.org/e107_plugins/radio/radio\.php\?search', 'q'),
    ]


class BitjamSong(AbstractBaseUrl):
    site = bitjam
    canonical_format = "http://www.bitfellas.org/e107_plugins/radio/radio.php?info&id=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?bitfellas\.org/e107_plugins/radio/radio\.php\?info', 'id'),
    ]


artcity = Site("ArtCity", url='http://artcity.bitfellas.org/', allowed_hostnames=['artcity.bitfellas.org'])


class ArtcityArtist(AbstractBaseUrl):
    site = artcity
    canonical_format = "http://artcity.bitfellas.org/index.php?a=artist&id=%s"
    tests = [
        querystring_match(r'https?://artcity\.bitfellas\.org/index\.php', 'id', othervars={'a': 'artist'}),
    ]


class ArtcityImage(AbstractBaseUrl):
    site = artcity
    canonical_format = "http://artcity.bitfellas.org/index.php?a=show&id=%s"
    tests = [
        querystring_match(r'https?://artcity\.bitfellas\.org/index\.php', 'id', othervars={'a': 'show'}),
    ]


class DeviantartUser(AbstractBaseUrl):
    site = Site("deviantART")
    canonical_format = "http://%s.deviantart.com"
    tests = [
        regex_match(r'https?://(.*)\.deviantart\.com/?'),
    ]


class MobygamesDeveloper(AbstractBaseUrl):
    site = Site("MobyGames", url='https://www.mobygames.com/')
    canonical_format = "https://www.mobygames.com/developer/sheet/view/developerId,%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?mobygames\.com/developer/sheet/view/developerId\,(\d+)'),
    ]


asciiarena = Site("AsciiArena", url='http://www.asciiarena.com/')


class AsciiarenaArtist(AbstractBaseUrl):
    site = asciiarena
    canonical_format = "http://www.asciiarena.com/info_artist.php?artist=%s&sort_by=filename"
    tests = [
        querystring_match(r'https?://(?:www\.)?asciiarena\.com/info_artist\.php', 'artist'),
    ]


class AsciiarenaCrew(AbstractBaseUrl):
    site = asciiarena
    canonical_format = "http://www.asciiarena.com/info_crew.php?crew=%s&sort_by=filename"
    tests = [
        querystring_match(r'https?://(?:www\.)?asciiarena\.com/info_crew\.php', 'crew'),
    ]


class AsciiarenaRelease(AbstractBaseUrl):
    site = asciiarena
    canonical_format = "http://www.asciiarena.com/info_release.php?filename=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?asciiarena\.com/info_release\.php', 'filename'),
    ]


scenesat = Site("SceneSat", long_name="SceneSat Radio", url='https://scenesat.com/')


class ScenesatAct(AbstractBaseUrl):
    site = scenesat
    canonical_format = "https://scenesat.com/act/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?scenesat\.com/act/(\d+)'),
    ]


class ScenesatTrack(AbstractBaseUrl):
    site = scenesat
    canonical_format = "https://scenesat.com/track/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?scenesat\.com/track/(\d+)'),
    ]


zxdemo = Site("ZXdemo", long_name="zxdemo.org", url='https://zxdemo.org/')


class ZxdemoAuthor(AbstractBaseUrl):
    site = zxdemo
    canonical_format = "https://zxdemo.org/author.php?id=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?zxdemo\.org/author\.php', 'id'),
    ]


class ZxdemoItem(AbstractBaseUrl):
    site = zxdemo
    canonical_format = "https://zxdemo.org/item.php?id=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?zxdemo\.org/item\.php', 'id'),
    ]


kestra_bitworld = Site(
    "Kestra BitWorld", classname="kestra_bitworld", url='http://janeway.exotica.org.uk/',
    allowed_hostnames=['janeway.exotica.org.uk']
)


class KestraBitworldRelease(AbstractBaseUrl):
    site = kestra_bitworld
    canonical_format = "http://janeway.exotica.org.uk/release.php?id=%s"
    tests = [
        querystring_match(r'https?://janeway\.exotica\.org\.uk/release\.php', 'id'),
    ]


class KestraBitworldAuthor(AbstractBaseUrl):
    site = kestra_bitworld
    canonical_format = "http://janeway.exotica.org.uk/author.php?id=%s"
    tests = [
        querystring_match(r'https?://janeway\.exotica\.org\.uk/author\.php', 'id'),
    ]


class KestraBitworldParty(AbstractBaseUrl):
    site = kestra_bitworld
    canonical_format = "http://janeway.exotica.org.uk/party.php?id=%s"
    tests = [
        querystring_match(r'https?://janeway\.exotica\.org\.uk/party\.php', 'id'),
    ]


sceneorg = Site("scene.org", classname="sceneorg")


class SceneOrgFile(AbstractBaseUrl):
    site = sceneorg

    # custom test for file_dl.php URLs, of the format:
    # http://www.scene.org/file_dl.php?url=ftp://ftp.scene.org/pub/parties/2009/stream09/in4k/moldtype.zip&id=523700
    file_dl_regex = re.compile(r'https?://(?:www\.)?scene\.org/file_dl\.php', re.I)

    def file_dl_match(urlstring, url):
        if SceneOrgFile.file_dl_regex.match(urlstring):
            # link is a file_dl.php link; extract the inner url, then recursively match on that
            querystring = urllib.parse.parse_qs(url.query)
            try:
                inner_url_string = querystring['url'][0]
                inner_url = urllib.parse.urlparse(inner_url_string)
                return SceneOrgFile.extract_param(inner_url_string, inner_url)
            except KeyError:
                return None

    tests = [
        file_dl_match,
        querystring_match(r'https?://(?:www\.)?scene\.org/file\.php', 'file'),
        urldecoded_regex_match(r'https?://files\.scene\.org/view(/.*)'),
        urldecoded_regex_match(r'https?://files\.scene\.org/get\:\w+\-\w+(/.*)'),
        urldecoded_regex_match(r'https?://files\.scene\.org/get(/.*)'),
        urldecoded_regex_match(r'https?://archive\.scene\.org/pub(/.*)'),
        urldecoded_regex_match(r'ftp://(?:ftp\.)?(?:nl\.)?scene\.org/pub(/.*)'),
        urldecoded_regex_match(r'ftp://(?:ftp\.)?(?:nl\.)?scene\.org(/mirrors/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*)'),
        urldecoded_regex_match(r'https?://ftp\.scene\.org/pub(/.*)'),
        urldecoded_regex_match(r'https?://http\.no\.scene\.org/scene\.org(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*)'),
        urldecoded_regex_match(r'https?://(?:http\.)?de\.scene\.org/pub(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*)'),
        urldecoded_regex_match(r'https?://http\.us\.scene\.org/pub/scene.org(/.*)'),
        urldecoded_regex_match(r'https?://http\.fr\.scene\.org(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.hu\.scene\.org/mirrors/scene.org(/.*)'),
        urldecoded_regex_match(r'https?://http\.hu\.scene\.org(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.pl\.scene\.org/pub/demos(/.*)'),
        urldecoded_regex_match(r'https?://http\.pl\.scene\.org/pub/demos(/.*)'),
        urldecoded_regex_match(r'ftp://ftp\.ua\.scene\.org/pub/mirrors/sceneorg(/.*)'),
    ]

    @property
    def info_url(self):
        return u"https://files.scene.org/view%s" % urllib.parse.quote(self.param.encode('iso-8859-1'))

    @property
    def auto_mirror_url(self):
        return u"https://files.scene.org/get%s" % urllib.parse.quote(self.param.encode('iso-8859-1'))

    def __str__(self):
        return self.info_url

    @property
    def nl_url(self):
        return u"ftp://ftp.scene.org/pub%s" % urllib.parse.quote(self.param.encode('iso-8859-1'))

    @property
    def nl_http_url(self):
        return u"http://archive.scene.org/pub%s" % urllib.parse.quote(self.param.encode('iso-8859-1'))

    @property
    def nl_https_url(self):
        return u"https://archive.scene.org/pub%s" % urllib.parse.quote(self.param.encode('iso-8859-1'))

    @property
    def download_url(self):
        return self.nl_url

    def as_download_link(self):
        return '''
            <div><a href="%s" class="primary">Download (scene.org)</a> -
            <a href="%s" class="secondary">file info</a></div>
        ''' % (
            escape(self.auto_mirror_url), escape(self.info_url)
        )


class AmigascneFile(AbstractBaseUrl):
    site = Site("amigascne.org", classname="amigascne")
    canonical_format = "ftp://ftp.amigascne.org/pub/amiga%s"
    tests = [
        regex_match(r'(?:http|ftp|https)://(?:\w+\@)?(?:ftp\.)?amigascne\.org/pub/amiga(/.*)'),
        regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/mirrors/amigascne(/.*)'),
        regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub/mirrors/amigascne(/.*)'),
        regex_match(r'ftp://ftp\.de\.scene\.org/pub/mirrors/amigascne(/.*)'),
        regex_match(r'https?://(?:http\.)?de\.scene\.org/pub/mirrors/amigascne(/.*)'),
        regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org/mirrors/amigascne(/.*)'),
        regex_match(r'ftp://ftp\.us\.scene\.org/scene.org/mirrors/amigascne(/.*)'),
        regex_match(r'https?://http\.us\.scene\.org/pub/scene.org/mirrors/amigascne(/.*)'),
    ]

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


class PaduaOrgFile(AbstractBaseUrl):
    site = Site("padua.org", long_name="ftp.padua.org", classname="padua")
    canonical_format = "ftp://ftp.padua.org/pub/c64%s"
    tests = [
        regex_match(r'ftp://ftp\.padua\.org/pub/c64(/.*)'),
        regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/mirrors/padua(/.*)'),
        regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub/mirrors/padua(/.*)'),
        regex_match(r'ftp://ftp\.de\.scene\.org/pub/mirrors/padua(/.*)'),
        regex_match(r'https?://(?:http\.)?de\.scene\.org/pub/mirrors/padua(/.*)'),
        regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org/mirrors/padua(/.*)'),
        regex_match(r'ftp://ftp\.us\.scene\.org/scene.org/mirrors/padua(/.*)'),
        regex_match(r'https?://http\.us\.scene\.org/pub/scene.org/mirrors/padua(/.*)'),
    ]

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


class ModlandFile(AbstractBaseUrl):
    site = Site("Modland")
    canonical_format = "ftp://ftp.modland.com%s"

    # need to fiddle querystring_match to prepend a slash to the matched query param
    def exotica_querystring_match():
        inner_fn = querystring_match(r'https?://files.exotica.org.uk/modland/\?', 'file')

        def wrapped_fn(*args):
            result = inner_fn(*args)
            if result is None:
                return None
            else:
                return '/' + result

        return wrapped_fn

    tests = [
        regex_match(r'(?:ftp|http|https)://(?:ftp\.)?modland\.com(/.*)'),
        regex_match(r'(?:ftp|http|https)://modland\.ziphoid\.com(/.*)'),
        regex_match(r'ftp://hangar18\.exotica\.org\.uk/modland(/.*)'),
        regex_match(r'ftp://aero.exotica.org.uk/pub/mirrors/modland(/.*)'),
        regex_match(r'ftp://ftp\.amigascne\.org/mirrors/ftp\.modland\.com(/.*)'),
        regex_match(r'ftp://ftp\.rave\.ca(/.*)'),
        regex_match(r'ftp://modland\.mindkiller\.com/modland(/.*)'),
        regex_match(r'https?://modland\.antarctica\.no(/.*)'),
        exotica_querystring_match(),
    ]

    @property
    def mirror_links(self):
        links = [
            '<li><a class="country country_uk" href="%s">uk</a></li>' % escape(self.uk_url),
            '<li><a href="%s" class="country country_se">se</a></li>' % escape(self.se_url),
            '<li><a href="%s" class="country country_us">us</a></li>' % escape(self.us_url),
            # '<li><a href="%s" class="country country_ca">ca</a></li>' % escape(self.ca_url),
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

    # @property
    # def ca_url(self):
    #     return "ftp://ftp.rave.ca%s" % self.param

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


fujiology = Site(
    "Fujiology", long_name="the Fujiology Archive", url='https://ftp.untergrund.net/',
    allowed_schemes=['https', 'ftp'], allowed_hostnames=['ftp.untergrund.net', 'fujiology.untergrund.net']
)


class FujiologyFile(AbstractBaseUrl):
    site = fujiology
    canonical_format = "https://ftp.untergrund.net/users/ltk_tscc/fujiology%s"
    tests = [
        regex_match(r'(?:https|ftp)://(?:fujiology\.|ftp\.)untergrund\.net/users/ltk_tscc/fujiology(/.*)'),
    ]
    download_link_label = "Fujiology @ untergrund.net"


class FujiologyFolder(AbstractBaseUrl):
    site = fujiology
    canonical_format = "https://ftp.untergrund.net/users/ltk_tscc/fujiology%s"
    tests = [
        regex_match(
            r'(?:https|ftp)://(?:fujiology\.|ftp\.)?untergrund\.net/users/ltk_tscc/fujiology(/.*)',
            re.I, add_slash=True
        ),
    ]


class UntergrundFile(AbstractBaseUrl):
    site = Site(
        "untergrund.net", classname="untergrund", url='https://ftp.untergrund.net/',
        allowed_schemes=['https', 'ftp'], allowed_hostnames=['ftp.untergrund.net', 'untergrund.net']
    )
    canonical_format = "https://ftp.untergrund.net%s"
    tests = [
        regex_match(r'(?:https|ftp)://(?:ftp\.)?untergrund\.net(/.*)'),
    ]


class DemopartyNetParty(AbstractBaseUrl):
    site = Site("demoparty.net", classname="demoparty_net", url='http://www.demoparty.net/')
    canonical_format = "http://www.demoparty.net/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?demoparty\.net/(.+)'),
    ]


class LanyrdEvent(AbstractBaseUrl):
    site = Site("Lanyrd", url='http://lanyrd.com/')
    canonical_format = "http://lanyrd.com/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?lanyrd\.com/(\d+/[^/]+)'),
    ]


class SlengpungParty(AbstractBaseUrl):
    site = slengpung
    canonical_format = "http://www.slengpung.com/?eventid=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?slengpung\.com/v[\d_]+/parties\.php', 'id'),
        querystring_match(r'https?://(?:www\.)?slengpung\.com/', 'eventid'),
    ]


class PouetParty(AbstractBaseUrl):
    site = pouet

    def match_pouet_party(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?pouet\.net/party\.php', re.I)
        if regex.match(urlstring):
            querystring = urllib.parse.parse_qs(url.query)
            try:
                return "%s/%s" % (querystring['which'][0], querystring['when'][0])
            except KeyError:
                return None

    tests = [match_pouet_party]

    def __str__(self):
        (id, year) = self.param.split('/')
        return u"http://www.pouet.net/party.php?which=%s&when=%s" % (id, year)


class CsdbEvent(AbstractBaseUrl):
    site = csdb
    canonical_format = "https://csdb.dk/event/?id=%s"
    tests = [
        querystring_match(r'https?://noname\.c64\.org/csdb/event/', 'id'),
        querystring_match(r'https?://(?:www\.)?csdb\.dk/event/', 'id'),
    ]


class BreaksAmigaParty(AbstractBaseUrl):
    site = Site("Break's Amiga Collection", classname="breaks_amiga", url='http://arabuusimiehet.com/')
    canonical_format = "http://arabuusimiehet.com/break/amiga/index.php?mode=party&partyid=%s"
    tests = [
        querystring_match(
            r'https?://(?:www\.)?arabuusimiehet\.com/break/amiga/index\.php',
            'partyid', othervars={'mode': 'party'}
        ),
    ]


class SceneOrgFolder(AbstractBaseUrl):
    site = sceneorg
    tests = [
        urldecoded_regex_match(r'https?://files\.scene\.org/browse(/.*)', add_slash=True),
        querystring_match(r'https?://(?:www\.)?scene\.org/dir\.php', 'dir'),
        urldecoded_regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org/pub(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.(?:nl\.)?scene\.org(/mirrors/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.no\.scene\.org/scene\.org(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/demos/scene(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.jp\.scene\.org/pub/scene(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.de\.scene\.org/pub(/.*)', add_slash=True),
        urldecoded_regex_match(r'https?://(?:http\.)?de\.scene\.org/pub(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/pub/scene.org(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.us\.scene\.org/scene.org(/.*)', add_slash=True),
        urldecoded_regex_match(r'https?://http\.us\.scene\.org/pub/scene.org(/.*)', add_slash=True),
        urldecoded_regex_match(r'https?://http\.fr\.scene\.org(/.*)', add_slash=True),
        urldecoded_regex_match(r'ftp://ftp\.pl\.scene\.org/pub/demos(/.*)', add_slash=True),
        urldecoded_regex_match(r'https?://http\.pl\.scene\.org/pub/demos(/.*)', add_slash=True),
    ]

    def __str__(self):
        return u"https://files.scene.org/browse%s" % urllib.parse.quote(self.param.encode('iso-8859-1'))


class ZxdemoParty(AbstractBaseUrl):
    site = zxdemo
    canonical_format = "https://zxdemo.org/party.php?id=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?zxdemo\.org/party\.php', 'id'),
    ]


youtube = Site("YouTube")


class YoutubeVideo(AbstractBaseUrl):
    site = youtube

    def match_long_url(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?youtube\.com/watch\?', re.I)
        if regex.match(urlstring):
            querystring = urllib.parse.parse_qs(url.query)
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
            querystring = urllib.parse.parse_qs(url.query)
            if 'start' in querystring:
                return "%s/%s" % (v, querystring['start'][0])
            else:
                return v

    def match_short_url(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?youtu\.be/([\w\-\_]+)', re.I)
        m = regex.match(urlstring)
        if m:
            v = m.group(1)
            querystring = urllib.parse.parse_qs(url.query)
            if 't' in querystring:
                return "%s/%s" % (v, querystring['t'][0])
            else:
                return v

    tests = [
        match_long_url,
        match_embed_url,
        match_short_url,
    ]
    is_streaming_video = True

    oembed_base_url = "https://www.youtube.com/oembed"
    oembed_add_format_parameter = True

    supports_embed_data = True

    def __str__(self):
        if '/' in self.param:
            (id, timestamp) = self.param.split('/')
            return u"https://www.youtube.com/watch?v=%s&t=%s" % (id, timestamp)
        else:
            return u"https://www.youtube.com/watch?v=%s" % self.param

    def get_embed_data(self, oembed_only=False):
        embed_data = {}

        if not oembed_only:
            url = str(self)
            response = urllib.request.urlopen(url)
            response_data = response.read()
            response.close()
            soup = BeautifulSoup(response_data, features="html.parser")
            embed_data['video_width'] = int(soup.find('meta', {'property': 'og:video:width'})['content'])
            embed_data['video_height'] = int(soup.find('meta', {'property': 'og:video:height'})['content'])

        oembed_thumbnail_url = self.get_oembed_url(max_width=400, max_height=300)
        response = urllib.request.urlopen(oembed_thumbnail_url)
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


class YoutubeUser(AbstractBaseUrl):
    site = youtube
    canonical_format = "https://www.youtube.com/user/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?youtube\.com/user/([^\/\?]+)'),
    ]


class YoutubeChannel(AbstractBaseUrl):
    site = youtube
    canonical_format = "https://www.youtube.com/channel/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?youtube\.com/channel/([^\/\?]+)'),
    ]


vimeo = Site("Vimeo", url='https://vimeo.com/')


class VimeoVideo(AbstractBaseUrl):
    site = vimeo
    canonical_format = "https://vimeo.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?vimeo\.com/(\d+)'),
    ]
    is_streaming_video = True

    oembed_base_url = "https://vimeo.com/api/oembed.json"
    oembed_add_format_parameter = False

    supports_embed_data = True

    def get_embed_data(self):
        embed_data = {}

        oembed_thumbnail_url = self.get_oembed_url(max_width=400, max_height=300)
        response = urllib.request.urlopen(oembed_thumbnail_url)
        response_data = response.read()
        response.close()
        oembed_data = json.loads(response_data)
        embed_data['thumbnail_url'] = oembed_data['thumbnail_url']
        embed_data['thumbnail_width'] = oembed_data['thumbnail_width']
        embed_data['thumbnail_height'] = oembed_data['thumbnail_height']

        oembed_url = self.get_oembed_url()
        response = urllib.request.urlopen(oembed_url)
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
            '<iframe width="{}" height="{}" src="{}" frameborder="0" webkitallowfullscreen '
            'mozallowfullscreen allowfullscreen></iframe>',
            width, height, embed_url
        )


class VimeoUser(AbstractBaseUrl):
    site = vimeo
    canonical_format = "https://vimeo.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?vimeo\.com/([\w-]+)/?$'),
    ]


class DemosceneTvVideo(AbstractBaseUrl):
    site = Site("Demoscene.tv", classname="demoscene_tv", url='http://demoscene.tv/')
    canonical_format = "http://demoscene.tv/page.php?id=172&vsmaction=view_prod&id_prod=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?demoscene\.tv/prod\.php', 'id_prod'),
        querystring_match(
            r'https?://(?:www\.)?demoscene\.tv/page\.php', 'id_prod',
            othervars={'id': '172', 'vsmaction': 'view_prod'}
        ),
    ]
    is_streaming_video = True


class CappedVideo(AbstractBaseUrl):
    site = Site("Capped.TV", classname="capped", url='http://capped.tv/')
    canonical_format = "http://capped.tv/%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?capped\.tv/playeralt\.php', 'vid'),
        regex_match(r'https?://(?:www\.)?capped\.tv/([-_\w]+)$'),
    ]
    is_streaming_video = True


class DhsVideoDbVideo(AbstractBaseUrl):
    site = Site("DHS VideoDB", classname="dhs_videodb", url='http://dhs.nu/')
    canonical_format = "http://dhs.nu/video.php?ID=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?dhs\.nu/video.php', 'ID'),
    ]


class FacebookPage(AbstractBaseUrl):
    site = Site("Facebook", url='https://www.facebook.com/')
    canonical_format = "https://www.facebook.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?facebook\.com/(.+)'),
    ]


googleplus = Site(
    "Google+", classname="googleplus", url='https://plus.google.com/', allowed_hostnames=['plus.google.com']
)


class GooglePlusPage(AbstractBaseUrl):
    site = googleplus
    canonical_format = "https://plus.google.com/%s/"
    tests = [
        regex_match(r'https?://plus\.google\.com/(\d+)'),
    ]


class GooglePlusEvent(AbstractBaseUrl):
    site = googleplus
    canonical_format = "https://plus.google.com/u/0/events/%s"
    tests = [
        regex_match(r'https?://plus\.google\.com/u/0/events/(\w+)'),
    ]


soundcloud = Site("SoundCloud", url='https://soundcloud.com/')


class SoundcloudUser(AbstractBaseUrl):
    site = soundcloud
    canonical_format = "https://soundcloud.com/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?soundcloud\.com/([^\/]+)'),
    ]


hearthis = Site("hearthis.at", classname="hearthis", url='https://hearthis.at/')


class HearthisUser(AbstractBaseUrl):
    site = hearthis
    canonical_format = "https://hearthis.at/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?hearthis\.at/([^\/]+)'),
    ]


class SoundcloudTrack(AbstractBaseUrl):
    site = soundcloud
    canonical_format = "https://soundcloud.com/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?soundcloud\.com/([^\/]+/[^\/]+)'),
    ]


class HearthisTrack(AbstractBaseUrl):
    site = hearthis
    canonical_format = "https://hearthis.at/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?hearthis\.at/([^\/]+/[^\/]+)'),
    ]


discogs = Site("Discogs", url='https://www.discogs.com/')


class DiscogsArtist(AbstractBaseUrl):
    site = discogs
    canonical_format = "https://www.discogs.com/artist/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?discogs\.com/artist/(.+)'),
    ]


class DiscogsLabel(AbstractBaseUrl):
    site = discogs
    canonical_format = "https://www.discogs.com/label/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?discogs\.com/label/(.+)'),
    ]


class DiscogsRelease(AbstractBaseUrl):
    site = discogs

    def match_discogs_release(urlstring, url):
        regex = re.compile(r'https?://(?:www\.)?discogs\.com/([^\/]+)/release/(\d+)', re.I)
        match = regex.match(urlstring)
        if match:
            slug, id = match.groups()
            return "%s/%s" % (id, slug)

    tests = [match_discogs_release]

    def __str__(self):
        (id, slug) = self.param.split('/')
        return u"http://www.discogs.com/%s/release/%s" % (slug, id)


modarchive = Site("ModArchive", long_name="The Mod Archive")


class ModarchiveMember(AbstractBaseUrl):
    site = modarchive
    canonical_format = "https://modarchive.org/member.php?%s"
    tests = [
        regex_match(r'https?://(?:www\.)?modarchive\.org/member\.php\?(\d+)'),
        querystring_match(
            r'https?://(?:www\.)?modarchive\.org/index\.php',
            'query', othervars={'request': 'view_profile'}
        ),
    ]


class ModarchiveModule(AbstractBaseUrl):
    site = modarchive
    canonical_format = "https://modarchive.org/module.php?%s"
    tests = [
        regex_match(r'https?://(?:www\.|lite\.)?modarchive\.org/module\.php\?(\d+)'),
        querystring_match(
            r'https?://(?:www\.|lite\.)?modarchive\.org/index\.php',
            'query', othervars={'request': 'view_by_moduleid'}
        ),
        querystring_match(r'https?://(?:www\.|lite\.)?modarchive\.org/data/downloads\.php', 'moduleid'),
        querystring_match(r'https?://api.modarchive\.org/downloads\.php', 'moduleid'),
    ]


class WikipediaPage(AbstractBaseUrl):
    site = Site("Wikipedia")
    canonical_format = "%s"  # entire URL is stored as parameter, to cover all language domains
    tests = [
        regex_match(r'(https?://\w+\.wikipedia\.org/.*)'),
    ]


class SpeccyWikiPage(AbstractBaseUrl):
    site = Site("SpeccyWiki", url='http://speccy.info/')
    canonical_format = "http://speccy.info/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?speccy.info/(.+)'),
    ]


class AtarimaniaPage(AbstractBaseUrl):
    site = Site("Atarimania", url='http://www.atarimania.com/')
    canonical_format = "http://www.atarimania.com/%s.html"
    tests = [
        regex_match(r'https?://(?:www\.)?atarimania.com/(.+)\.html'),
    ]


pushnpop = Site("Push'n'Pop", classname="pushnpop", url='http://pushnpop.net/')


class PushnpopProduction(AbstractBaseUrl):
    site = pushnpop
    canonical_format = "http://pushnpop.net/prod-%s.html"
    tests = [
        regex_match(r'https?://(?:www\.)?pushnpop\.net/prod-(\d+)\.html'),
    ]


class PushnpopParty(AbstractBaseUrl):
    site = pushnpop
    canonical_format = "http://pushnpop.net/parties-%s.html"
    tests = [
        regex_match(r'https?://(?:www\.)?pushnpop\.net/parties-(\d+)\.html'),
    ]


class PushnpopGroup(AbstractBaseUrl):
    site = pushnpop
    canonical_format = "http://pushnpop.net/group-%s.html"
    tests = [
        regex_match(r'https?://(?:www\.)?pushnpop\.net/group-(\d+)\.html'),
    ]


class PushnpopProfile(AbstractBaseUrl):
    site = pushnpop
    canonical_format = "http://pushnpop.net/profile-%s.html"
    tests = [
        regex_match(r'https?://(?:www\.)?pushnpop\.net/profile-(\d+)\.html'),
    ]


zxart = Site("ZXArt", url='http://zxart.ee/')


class ZxArtAuthor(AbstractBaseUrl):
    site = zxart
    canonical_format = "http://zxart.ee/eng/authors/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/authors/(\w/[^\/]+)(/qid:\d+)?/?'),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/avtory/(\w/[^\/]+)(/qid:\d+)?/?'),
    ]


class ZxArtPicture(AbstractBaseUrl):
    site = zxart
    canonical_format = "http://zxart.ee/eng/graphics/authors/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/authors/([^\/]+/[^\/]+/[^\/]+)/?'),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/avtory/([^\/]+/[^\/]+/[^\/]+)/?'),
    ]


class ZxArtMusic(AbstractBaseUrl):
    site = zxart
    canonical_format = "http://zxart.ee/eng/music/authors/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/authors/([^\/]+/[^\/]+/[^\/]+)/?'),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/avtory/([^\/]+/[^\/]+/[^\/]+)/?'),
    ]


class ZxArtPartyGraphics(AbstractBaseUrl):
    site = zxart
    canonical_format = "http://zxart.ee/eng/graphics/parties/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/graphics/parties/([^\/]+/[^\/]+)/?'),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/grafika/pati/([^\/]+/[^\/]+)/?'),
    ]


class ZxArtPartyMusic(AbstractBaseUrl):
    site = zxart
    canonical_format = "http://zxart.ee/eng/music/parties/%s/"
    tests = [
        regex_match(r'https?://(?:www\.)?zxart\.ee/eng/music/parties/([^\/]+/[^\/]+)/?'),
        regex_match(r'https?://(?:www\.)?zxart\.ee/rus/muzyka/pati/([^\/]+/[^\/]+)/?'),
    ]


hall_of_light = Site(
    "Hall Of Light", classname="hall_of_light", url='http://hol.abime.net/', allowed_hostnames=['hol.abime.net']
)


class HallOfLightGame(AbstractBaseUrl):
    site = hall_of_light
    canonical_format = "http://hol.abime.net/%s"
    tests = [
        regex_match(r'https?://hol\.abime\.net/(\d+)'),
    ]


class HallOfLightArtist(AbstractBaseUrl):
    site = hall_of_light
    canonical_format = "http://hol.abime.net/hol_search.php?N_ref_artist=%s"
    tests = [
        querystring_match(r'https?://hol\.abime\.net/hol_search\.php', 'N_ref_artist'),
    ]


spotify = Site(
    "Spotify", url='https://play.spotify.com/', allowed_hostnames=['open.spotify.com', 'play.spotify.com']
)


class SpotifyArtist(AbstractBaseUrl):
    site = spotify
    canonical_format = "https://play.spotify.com/artist/%s"
    tests = [
        regex_match(r'https?://(?:open|play)\.spotify\.com/artist/(\w+)'),
    ]


class SpotifyTrack(AbstractBaseUrl):
    site = spotify
    canonical_format = "https://play.spotify.com/track/%s"
    tests = [
        regex_match(r'https?://(?:open|play)\.spotify\.com/track/(\w+)'),
    ]


github = Site("GitHub", url='https://github.com/', allowed_hostnames=['github.com'])


class GithubAccount(AbstractBaseUrl):
    site = github
    canonical_format = "https://github.com/%s"
    tests = [
        regex_match(r'https?://github\.com/([^\/]+)/?$'),
    ]


class GithubRepo(AbstractBaseUrl):
    site = github
    canonical_format = "https://github.com/%s"
    tests = [
        regex_match(r'https?://github\.com/([^\/]+/[^\/]+)/?$'),
    ]


class GithubDirectory(AbstractBaseUrl):
    site = github

    def __str__(self):
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


class InternetArchivePage(AbstractBaseUrl):
    site = Site(
        "Internet Archive", long_name="the Internet Archive", classname="internetarchive",
        url='https://archive.org/'
    )
    canonical_format = "https://archive.org/details/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?archive.org/details/(.+)'),
    ]


class WaybackMachinePage(AbstractBaseUrl):
    site = Site(
        "Wayback Machine", long_name="the Wayback Machine", classname="waybackmachine",
        url='https://web.archive.org/'
    )
    canonical_format = "https://web.archive.org/web/%s"
    tests = [
        regex_match(r'https?://web\.archive.org/web/(.+)'),
    ]


class StonishDisk(AbstractBaseUrl):
    site = Site("Stonish", url='http://stonish.net/')
    canonical_format = "http://stonish.net/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?stonish\.net/([\w\-]+\#st\d+)'),
    ]


class ZxTunesArtist(AbstractBaseUrl):
    site = Site("ZXTunes", url='http://zxtunes.com/')
    canonical_format = "http://zxtunes.com/author.php?id=%s&ln=eng"
    tests = [
        querystring_match(r'https?://(?:www\.)?zxtunes\.com/author\.php', 'id'),
    ]


gameboy_demospotting = Site(
    "Gameboy Demospotting", classname="gameboydemospotting", url='http://gameboy.modermodemet.se/',
    allowed_hostnames=['gameboy.modermodemet.se']
)


class GameboyDemospottingAuthor(AbstractBaseUrl):
    site = gameboy_demospotting
    canonical_format = "http://gameboy.modermodemet.se/en/author/%s"
    tests = [
        regex_match(r'https?://gameboy\.modermodemet\.se/\w+/author/(\d+)'),
    ]


class GameboyDemospottingDemo(AbstractBaseUrl):
    site = gameboy_demospotting
    canonical_format = "http://gameboy.modermodemet.se/en/demo/%s"
    tests = [
        regex_match(r'https?://gameboy\.modermodemet\.se/\w+/demo/(\d+)'),
    ]


pixeljoint = Site("Pixeljoint", url='http://pixeljoint.com/')


class PixeljointArtist(AbstractBaseUrl):
    site = pixeljoint
    canonical_format = "http://pixeljoint.com/p/%s.htm"
    tests = [
        regex_match(r'https?://(?:www\.)?pixeljoint\.com/p/(\d+)\.htm'),
    ]


class PixeljointImage(AbstractBaseUrl):
    site = pixeljoint
    canonical_format = "http://pixeljoint.com/pixelart/%s.htm"
    tests = [
        regex_match(r'https?://(?:www\.)?pixeljoint\.com/pixelart/(\d+)\.htm'),
    ]


plus4world = Site(
    "Plus/4 World", classname="plus4world", url='http://plus4world.powweb.com/',
    allowed_hostnames=['plus4world.powweb.com']
)


class Plus4WorldProduction(AbstractBaseUrl):
    site = plus4world
    canonical_format = "http://plus4world.powweb.com/software/%s"
    tests = [
        regex_match(r'https?://plus4world\.powweb\.com/software/(\w+)'),
    ]


class Plus4WorldGroup(AbstractBaseUrl):
    site = plus4world
    canonical_format = "http://plus4world.powweb.com/groups/%s"
    tests = [
        regex_match(r'https?://plus4world\.powweb\.com/groups/(\w+)'),
    ]


class Plus4WorldMember(AbstractBaseUrl):
    site = plus4world
    canonical_format = "http://plus4world.powweb.com/members/%s"
    tests = [
        regex_match(r'https?://plus4world\.powweb\.com/members/(\w+)'),
    ]


bandcamp = Site("Bandcamp")


class BandcampArtist(AbstractBaseUrl):
    site = bandcamp
    canonical_format = "https://%s.bandcamp.com/"
    tests = [
        regex_match(r'https?://([\w-]+)\.bandcamp\.com/?$'),
    ]


class BandcampTrack(AbstractBaseUrl):
    site = bandcamp

    def match_bandcamp_release(urlstring, url):
        regex = re.compile(r'https?://([\w-]+)\.bandcamp\.com/track/([\w-]+)', re.I)
        match = regex.match(urlstring)
        if match:
            domain, name = match.groups()
            return "%s/%s" % (domain, name)

    tests = [match_bandcamp_release]

    def __str__(self):
        (domain, name) = self.param.split('/')
        return u"https://%s.bandcamp.com/track/%s" % (domain, name)


class TwitchChannel(AbstractBaseUrl):
    site = Site(
        "Twitch", url='https://twitch.tv/', allowed_hostnames=['m.twitch.tv', 'twitch.tv', 'www.twitch.tv']
    )
    canonical_format = "https://twitch.tv/%s"  # Channel name
    tests = [
        # Use (\w+) as Twitch does not accept `-` during registration
        regex_match(r'https?://m\.twitch\.tv/(\w+)'),  # Mobile version
        regex_match(r'https?://(?:www\.)?twitch\.tv/(\w+)'),
    ]


speccypl = Site("speccy.pl", classname="speccypl", url='http://speccy.pl/')


class SpeccyPlProduction(AbstractBaseUrl):
    site = speccypl
    canonical_format = "http://speccy.pl/archive/prod.php?id=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?speccy\.pl/archive/prod\.php', 'id'),
    ]


class SpeccyPlAuthor(AbstractBaseUrl):
    site = speccypl
    canonical_format = "http://speccy.pl/archive/author.php?id=%s"
    tests = [
        querystring_match(r'https?://(?:www\.)?speccy\.pl/archive/author\.php', 'id'),
    ]


class AtarikiEntry(AbstractBaseUrl):
    site = Site("Atariki")
    canonical_format = "http://atariki.krap.pl/index.php/%s"
    tests = [
        regex_match(r'https?://(?:www\.)?atariki\.krap\.pl/index\.php/(.*)'),
    ]


RELEASER_LINK_TYPES = [
    TwitterAccount, SceneidAccount, SlengpungUser, AmpAuthor,
    CsdbScener, CsdbGroup, NectarineArtist, NectarineGroup, BitjamAuthor, ArtcityArtist,
    MobygamesDeveloper, AsciiarenaArtist, AsciiarenaCrew, PouetGroup,
    ScenesatAct, ZxdemoAuthor, FacebookPage,
    PushnpopGroup, PushnpopProfile, SceneOrgFolder, FujiologyFolder,
    GooglePlusPage, SoundcloudUser, HearthisUser, YoutubeUser, YoutubeChannel, TwitchChannel,
    DeviantartUser, ModarchiveMember, WikipediaPage,
    SpeccyWikiPage, DiscogsArtist, DiscogsLabel,
    HallOfLightArtist, SpotifyArtist, KestraBitworldAuthor,
    GithubAccount, GithubRepo, AtarimaniaPage, GameboyDemospottingAuthor, PixeljointArtist,
    ZxArtAuthor, ZxTunesArtist, InternetArchivePage,
    Plus4WorldGroup, Plus4WorldMember, BandcampArtist, VimeoUser, SpeccyPlAuthor, AtarikiEntry,
    WaybackMachinePage, BaseUrl,
]

PRODUCTION_LINK_TYPES = [
    PouetProduction, CsdbRelease, ZxdemoItem,
    YoutubeVideo, VimeoVideo, DemosceneTvVideo, CappedVideo, DhsVideoDbVideo,
    AsciiarenaRelease, KestraBitworldRelease, StonishDisk, ArtcityImage,
    ScenesatTrack, ModlandFile, SoundcloudTrack, HearthisTrack, BandcampTrack, CsdbMusic, NectarineSong,
    ModarchiveModule, BitjamSong, PushnpopProduction, SpotifyTrack, Plus4WorldProduction,
    SpeccyPlProduction, AtarikiEntry,
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
    'PixeljointImage', 'ArtcityImage', 'Plus4WorldProduction', 'SpeccyPlProduction', 'AtarikiEntry'
]

PARTY_LINK_TYPES = [
    DemopartyNetParty, SlengpungParty, PouetParty,
    CsdbEvent, BreaksAmigaParty, SceneOrgFolder, FujiologyFolder, TwitterAccount, ZxdemoParty,
    PushnpopParty, KestraBitworldParty, YoutubeUser, YoutubeChannel, TwitchChannel,
    FacebookPage, GooglePlusPage, GooglePlusEvent, LanyrdEvent, WikipediaPage,
    SpeccyWikiPage, ZxArtPartyGraphics, ZxArtPartyMusic, AtarikiEntry, WaybackMachinePage, BaseUrl,
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
    url = urllib.parse.urlparse(urlstring)
    for link_type in link_types:
        link = link_type.match(urlstring, url)
        if link:
            return link
