from __future__ import absolute_import, unicode_literals

from .base import *

import io
from six.moves import urllib
from six import ensure_binary
from PIL import Image


SECRET_KEY = 'BOOOOM'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',  # don't use the intentionally slow default password hasher
)

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

MEDIA_ROOT = os.path.join(FILEROOT, 'test_media')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/2')

AWS_ACCESS_KEY_ID = 'AWS_K3Y'
AWS_SECRET_ACCESS_KEY = 'AWS_S3CR3T'

SCENEID_KEY = 'SCENEID_K3Y'
SCENEID_SECRET = 'SCENEID_S3CR3T'


# set up mock opener for urllib

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
    elif url == 'http://geocoder.demozoo.org/?q=Adlington%2C+Lancashire%2C+England%2C+United+Kingdom':  # pragma: no cover
        # this is used to verify that we don't look up locations that are unchanged
        raise Exception("Looking up Adlington is not allowed! :-)")
    elif url == 'http://geocoder.demozoo.org/?q=Royston+Vasey':
        body = "[]"
    elif url.startswith('https://www.youtube.com/oembed'):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if qs == {'url': ['https://www.youtube.com/watch?v=ldoVS0idTBw'], 'maxheight': ['300'], 'maxwidth': ['400'], 'format': ['json']}:
            body = r"""{
                "provider_name":"YouTube",
                "author_url":"https:\/\/www.youtube.com\/user\/sirhadley",
                "thumbnail_height":360,"thumbnail_width":480,"width":400,"height":225,
                "title":"Deliberate Ramming by Canal Boat - Henley July 2019","version":"1.0",
                "html":"\u003ciframe width=\"400\" height=\"225\" src=\"https:\/\/www.youtube.com\/embed\/ldoVS0idTBw?feature=oembed\" frameborder=\"0\" allow=\"accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture\" allowfullscreen\u003e\u003c\/iframe\u003e",
                "type":"video","author_name":"sirhadley",
                "thumbnail_url":"https:\/\/i.ytimg.com\/vi\/ldoVS0idTBw\/hqdefault.jpg",
                "provider_url":"https:\/\/www.youtube.com\/"
            }"""
        elif qs == {'url': ['https://www.youtube.com/watch?v=404'], 'maxheight': ['300'], 'maxwidth': ['400'], 'format': ['json']}:
            resp = urllib.response.addinfourl(
                io.StringIO("not found"),
                {},
                req.get_full_url()
            )
            resp.code = 404
            resp.msg = "Not found"
            return resp
        else:  # pragma: no cover
            raise Exception("No response defined for %s" % req.get_full_url())
    elif url == 'https://www.youtube.com/watch?v=ldoVS0idTBw':
        body = r"""<!DOCTYPE html>
        <html>
            <head>
                <meta property="og:type" content="video.other">
                <meta property="og:video:url" content="https://www.youtube.com/embed/ldoVS0idTBw">
                <meta property="og:video:secure_url" content="https://www.youtube.com/embed/ldoVS0idTBw">
                <meta property="og:video:type" content="text/html">
                <meta property="og:video:width" content="1280">
                <meta property="og:video:height" content="720">
            </head>
            <body></body>
        </html>
        """
    elif url == 'https://www.youtube.com/watch?v=404':
        resp = urllib.response.addinfourl(
            io.StringIO("not found"),
            {},
            req.get_full_url()
        )
        resp.code = 404
        resp.msg = "Not found"
        return resp
    elif url.startswith('https://vimeo.com/api/oembed.json'):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if qs == {'url': ['https://vimeo.com/3156959'], 'maxheight': ['300'], 'maxwidth': ['400']}:
            body = r"""{
                "type":"video","version":"1.0","provider_name":"Vimeo","provider_url":"https:\/\/vimeo.com\/","title":"Bathtub IV",
                "author_name":"Keith Loutit","author_url":"https:\/\/vimeo.com\/keithloutit","is_plus":"0","account_type":"pro",
                "html":"<iframe src=\"https:\/\/player.vimeo.com\/video\/3156959?app_id=122963\" width=\"400\" height=\"225\" frameborder=\"0\" allow=\"autoplay; fullscreen\" allowfullscreen title=\"Bathtub IV\"><\/iframe>",
                "width":400,"height":225,"duration":213,
                "description":"This is a personal project that would not have been possible without the support of the Westpac Rescue Helicopter Service.",
                "thumbnail_url":"https:\/\/i.vimeocdn.com\/video\/453022_295x166.webp",
                "thumbnail_width":295,"thumbnail_height":166,
                "thumbnail_url_with_play_button":"https:\/\/i.vimeocdn.com\/filter\/overlay?src0=https%3A%2F%2Fi.vimeocdn.com%2Fvideo%2F453022_295x166.webp&src1=http%3A%2F%2Ff.vimeocdn.com%2Fp%2Fimages%2Fcrawler_play.png",
                "upload_date":"2009-02-10 02:29:39","video_id":3156959,"uri":"\/videos\/3156959"
            }"""
        elif qs == {'url': ['https://vimeo.com/3156959']}:
            body = r"""{
                "type":"video","version":"1.0","provider_name":"Vimeo","provider_url":"https:\/\/vimeo.com\/","title":"Bathtub IV",
                "author_name":"Keith Loutit","author_url":"https:\/\/vimeo.com\/keithloutit","is_plus":"0","account_type":"pro",
                "html":"<iframe src=\"https:\/\/player.vimeo.com\/video\/3156959?app_id=122963\" width=\"480\" height=\"270\" frameborder=\"0\" allow=\"autoplay; fullscreen\" allowfullscreen title=\"Bathtub IV\"><\/iframe>",
                "width":480,"height":270,"duration":213,
                "description":"This is a personal project that would not have been possible without the support of the Westpac Rescue Helicopter Service.",
                "thumbnail_url":"https:\/\/i.vimeocdn.com\/video\/453022_295x166.webp",
                "thumbnail_width":295,"thumbnail_height":166,
                "thumbnail_url_with_play_button":"https:\/\/i.vimeocdn.com\/filter\/overlay?src0=https%3A%2F%2Fi.vimeocdn.com%2Fvideo%2F453022_295x166.webp&src1=http%3A%2F%2Ff.vimeocdn.com%2Fp%2Fimages%2Fcrawler_play.png",
                "upload_date":"2009-02-10 02:29:39","video_id":3156959,"uri":"\/videos\/3156959"
            }"""
        else:  # pragma: no cover
            raise Exception("No response defined for %s" % req.get_full_url())
    elif url == 'https://files.scene.org/api/adhoc/latest-files/?days=1':
        body = r"""{
            "success": true,
            "nextPage": 100,
            "nextPageURL": "https:\/\/files.scene.org\/api\/adhoc\/latest-files\/?days=1&page=100",
            "files": [
                {
                    "filename": "zz-t_01.diz",
                    "fullPath": "\/demos\/zz-t_01.diz",
                    "viewURL": "https:\/\/files.scene.org\/view\/demos\/zz-t_01.diz",
                    "size": 281,
                    "mirrors": {
                        "nl-ftp": "ftp:\/\/ftp.scene.org\/pub\/demos\/zz-t_01.diz",
                        "nl-http": "http:\/\/archive.scene.org\/pub\/demos\/zz-t_01.diz"
                    }
                }
            ]
        }"""
    elif url == 'https://files.scene.org/api/adhoc/latest-files/?days=1&page=100':
        body = r"""{
            "success": true,
            "files": [
                {
                    "filename": "lazarus-taxi-247-compo-version.diz",
                    "fullPath": "\/demos\/artists\/lazarus\/lazarus-taxi-247-compo-version.diz",
                    "viewURL": "https:\/\/files.scene.org\/view\/demos\/artists\/lazarus\/lazarus-taxi-247-compo-version.diz",
                    "size": 296,
                    "mirrors": {
                        "nl-ftp": "ftp:\/\/ftp.scene.org\/pub\/demos\/artists\/lazarus\/lazarus-taxi-247-compo-version.diz",
                        "nl-http": "http:\/\/archive.scene.org\/pub\/demos\/artists\/lazarus\/lazarus-taxi-247-compo-version.diz"
                    }
                }
            ]
        }"""
    elif url == 'https://files.scene.org/api/adhoc/latest-files/?days=999':
        body = r"""{
            "success": false
        }"""
    elif url == 'ftp://ftp.scene.org/pub/parties/2000/forever00/results.txt':
        body = r"""here are the results of Forever 2000"""
    elif url == 'http://kestra.exotica.org.uk/files/screenies/28000/154a.png':
        f = io.BytesIO()
        Image.new('P', (640, 480)).save(f, 'png')
        f.seek(0)
        resp = urllib.response.addinfourl(f, {'Content-Length': len(f.getvalue())}, req.get_full_url())
        f.seek(0)
        resp.code = 200
        resp.msg = "OK"
        return resp
    elif url == 'http://example.com/pretend-big-file.txt' or url == 'http://example.com/pretend-big-file.mod':
        resp = urllib.response.addinfourl(
            io.StringIO("this file claims to be big but isn't really"),
            {'Content-Length': 100000000},
            req.get_full_url()
        )
        resp.code = 200
        resp.msg = "OK"
        return resp
    elif url == 'http://example.com/real-big-file.txt':
        body = "I am a fish " * 1000000
    elif url == 'ftp://ftp.scene.org/pub/bigfile.txt':
        body = "I am a fish " * 1000000
    elif url == 'http://example.com/pondlife2.txt':
        body = "hello from pondlife2.txt"
    elif url == 'http://example.com/cybrev.mod':
        body = "hello from cybrev.mod"
    elif url == 'http://example.com/rubber.zip':
        path = os.path.join(FILEROOT, 'mirror', 'test_media', 'rubber.zip')
        with open(path, 'rb') as f:
            body = f.read()
    elif url == 'http://example.com/rubberbadimage.zip':
        path = os.path.join(FILEROOT, 'mirror', 'test_media', 'rubberbadimage.zip')
        with open(path, 'rb') as f:
            body = f.read()
    elif url == 'http://example.com/badzipfile.zip':
        body = "the grim reaper in a dress"
    elif url == 'http://example.com/badimage.png':
        body = "the grim reaper's back again, but this time she's got a hat"
    elif url == 'https://api.pouet.net/v1/group/?id=767':
        body = r"""
            {
                "success": true,
                "group": {
                    "id": "767",
                    "name": "Raww Arse",
                    "demozoo": "8881",
                    "prods": [
                        {
                            "groups": [
                                {"id": "767", "name": "Raww Arse"},
                                {"id": "325", "name": "Jumalauta"}
                            ],
                            "id": "2124",
                            "name": "Bunch Of Arse",
                            "releaseDate": "1999-09-15",
                            "download": "http:\/\/www.zxdemo.org\/files\/Boa.zip",
                            "screenshot": "https:\/\/content.pouet.net\/files\/screenshots\/00002\/00002124.gif"
                        }
                    ]
                }
            }
        """
    elif url == 'https://api.pouet.net/v1/group/?id=768':
        body = r"""
            {
                "success": true,
                "group": {
                    "id": "767",
                    "name": "Raww Arse",
                    "demozoo": "8881"
                }
            }
        """
    elif url == 'https://api.pouet.net/v1/group/?id=99999':
        body = r"""{"error": true}"""
    elif url == 'https://id.scene.org/oauth/token/':
        if req.get_method() == 'POST':
            if req.get_header('Authorization') != 'Basic U0NFTkVJRF9LM1k6U0NFTkVJRF9TM0NSM1Q=':  # pragma: no cover
                raise Exception("Bad authorization header for https://id.scene.org/oauth/token/ : %r" % req.get_header('Authorization'))

            expected_postdata = urllib.parse.parse_qs('code=123&grant_type=authorization_code&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F')
            actual_postdata = urllib.parse.parse_qs(req.data.decode('ascii'))
            if actual_postdata != expected_postdata:  # pragma: no cover
                raise Exception("Bad POST data: expected %r, got %r" % (expected_postdata, actual_postdata))

            body = r"""
                {
                    "access_token":"aaaaaaaaaaaaaaaa",
                    "expires_in":3600,"token_type":"Bearer","scope":"basic",
                    "refresh_token":"bbbbbbbbbbbbbbbb"
                }
            """
        else:  # pragma: no cover
            raise Exception("GET request not supported for id.scene.org")
    elif url == 'https://id.scene.org/api/3.0/me/?':
        if req.get_header('Authorization') != 'Bearer aaaaaaaaaaaaaaaa':  # pragma: no cover
            raise Exception("Bad authorization header for https://id.scene.org/api/3.0/me/")
        body = r"""
            {"success":true,"user":{"id":2260,"first_name":"Matt","last_name":"Westcott","display_name":"gasman"}}
        """

    else:  # pragma: no cover
        raise Exception("No response defined for %s" % req.get_full_url())

    resp = urllib.response.addinfourl(
        io.BytesIO(ensure_binary(body)), {}, req.get_full_url()
    )
    resp.code = 200
    resp.msg = "OK"
    return resp


class MockHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return mock_response(req)


class MockHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return mock_response(req)


class MockFTPHandler(urllib.request.FTPHandler):
    def ftp_open(self, req):
        return mock_response(req)


urllib.request.install_opener(urllib.request.build_opener(MockHTTPHandler, MockHTTPSHandler, MockFTPHandler))


COVERAGE_REPORT_HTML_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'coverage')
COVERAGE_MODULE_EXCLUDES = [
    'tests$', 'settings$', 'urls$', '^django',
    '^compressor', '^debug_toolbar', 'migrations',
    '^rest_framework', '^south', '^taggit', '^treebeard'
]

ZXDEMO_PLATFORM_IDS = [1]
