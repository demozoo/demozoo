from .base import *

import urllib2
from StringIO import StringIO


SECRET_KEY = 'BOOOOM'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',  # don't use the intentionally slow default password hasher
)

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

MEDIA_ROOT = os.path.join(FILEROOT, 'test_media')


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
    elif url == 'http://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DldoVS0idTBw&maxheight=300&maxwidth=400&format=json':
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
    elif url == 'https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F3156959&maxheight=300&maxwidth=400':
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
    elif url == 'https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F3156959':
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
    else:
        raise Exception("No response defined for %s" % req.get_full_url())

    resp = urllib2.addinfourl(StringIO(body), None, req.get_full_url())
    resp.code = 200
    resp.msg = "OK"
    return resp


class MockHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        return mock_response(req)


class MockHTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        return mock_response(req)


urllib2.install_opener(urllib2.build_opener(MockHTTPHandler))
urllib2.install_opener(urllib2.build_opener(MockHTTPSHandler))

try:
    from .test_local import *
except ImportError:
    pass
