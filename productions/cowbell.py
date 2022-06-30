import re

from django.forms import Media
from django.templatetags.static import static


# Cowbell <https://demozoo.github.io/cowbell/> integration

PLAYERS_BY_FILETYPE = {
    'stc': (
        'Cowbell.Player.ZXSTC', {},
        Media(js=[
            'productions/js/cowbell/cowbell.min.js',
            'productions/js/cowbell/ay_chip.min.js',
            'productions/js/cowbell/zx.min.js'
        ])
    ),
    'pt3': (
        'Cowbell.Player.ZXPT3', {},
        Media(js=[
            'productions/js/cowbell/cowbell.min.js',
            'productions/js/cowbell/ay_chip.min.js',
            'productions/js/cowbell/zx.min.js'
        ])
    ),
    'sqt': (
        'Cowbell.Player.ZXSQT', {},
        Media(js=[
            'productions/js/cowbell/cowbell.min.js',
            'productions/js/cowbell/ay_chip.min.js',
            'productions/js/cowbell/zx.min.js'
        ])
    ),
    'pyg': (  # PSG format configured with YM / Atari ST parameters
        'Cowbell.Player.PSG', {
            'ayFrequency': 2000000, 'ayMode': 'YM'
        },
        Media(js=[
            'productions/js/cowbell/cowbell.min.js',
            'productions/js/cowbell/ay_chip.min.js',
        ])
    ),
    'vtx': (
        'Cowbell.Player.VTX', {},
        Media(js=[
            'productions/js/cowbell/cowbell.min.js',
            'productions/js/cowbell/ay_chip.min.js',
            'productions/js/cowbell/vtx.min.js'
        ])
    ),
    'mp3': ('Cowbell.Player.Audio', {}, Media(js=['productions/js/cowbell/cowbell.min.js'])),
    'ogg': ('Cowbell.Player.Audio', {}, Media(js=['productions/js/cowbell/cowbell.min.js'])),
    'wav': ('Cowbell.Player.Audio', {}, Media(js=['productions/js/cowbell/cowbell.min.js'])),
    'opus': ('Cowbell.Player.Audio', {}, Media(js=['productions/js/cowbell/cowbell.min.js'])),
    'flac': ('Cowbell.Player.Audio', {}, Media(js=['productions/js/cowbell/cowbell.min.js'])),
    'openmpt': ('Cowbell.Player.OpenMPT', {
        'pathToLibOpenMPT': static('productions/js/cowbell/libopenmpt.js'),
    }, Media(js=[
        'productions/js/cowbell/cowbell.min.js', 'productions/js/cowbell/openmpt.min.js'
    ])),
    'sid': (
        'Cowbell.Player.JSSID', {},
        Media(js=[
            'productions/js/cowbell/cowbell.min.js', 'productions/js/cowbell/jssid.min.js'
        ])
    ),
    'sap': (
        'Cowbell.Player.ASAP', {},
        Media(js=[
            'productions/js/cowbell/cowbell.min.js', 'productions/js/cowbell/asap.min.js'
        ])
    ),
}

ZXDEMO_MUSIC = re.compile(r'https://files\.zxdemo\.org/.*\.(stc|pt3|vtx|sqt|pyg)$', re.I)
ABSENCEHQ_PYG_MUSIC = re.compile(r'https://absencehq.de/atari/.*\.(pyg)', re.I)
ZX_MUSIC = re.compile(r'.*\.(stc|pt3|vtx|sqt)$', re.I)
STREAMING_MUSIC = re.compile(r'.*\.(mp3|ogg|wav|opus|flac)$', re.I)
OPENMPT_MUSIC = re.compile(
    r'.*\.(mod|s3m|xm|it|mptm|stm|nst|m15|stk|wow|ult|669|mtm|med|far|mdl|ams|dsm|amf|okt|dmf|ptm'
    r'|psm|mt2|dbm|digi|imf|j2b|gdm|umx|plm|mo3|xpk|ppm|mmcmp|sfx|sfx2|mms|pt36|nt|ft|fmt|dsym'
    r'|symmod)$',
    re.I
)
# SID files on Modland have the extension .psid; .sid files on there are actually Amiga Sidmon tracker files
PSID_MUSIC = re.compile(r'.*\.psid$', re.I)
NONSTANDARD_MODLAND_EXTENSIONS = re.compile(r'.*\.(mmd0|mmd1|mmd2|mmd3)', re.I)

# stuff mirrored on media.demozoo.org/music
MEDIA_DEMOZOO_MUSIC = re.compile(r'https://media\.demozoo\.org/music/.*\.(mod|s3m|xm|it|sid|sap)$', re.I)


def identify_link_as_track(link):
    # return a (filetype, url) tuple for this link, or (None, None) if it can't be identified as one

    if link.is_download_link:
        if link.link_class == 'SceneOrgFile':
            match = STREAMING_MUSIC.match(link.parameter)
            if match:
                filetype = match.group(1).lower()
                url = link.link.nl_https_url
                return (filetype, url)

        elif link.link_class == 'ModlandFile':
            match = OPENMPT_MUSIC.match(link.parameter)
            if match:
                filetype = 'openmpt'
                url = 'https://modland.ziphoid.com%s' % link.parameter
                return (filetype, url)

            match = NONSTANDARD_MODLAND_EXTENSIONS.match(link.parameter)
            if match:
                filetype = 'openmpt'
                url = 'https://modland.ziphoid.com%s' % link.parameter
                return (filetype, url)

            match = ZX_MUSIC.match(link.parameter)
            if match:
                filetype = match.group(1).lower()
                url = 'https://modland.ziphoid.com%s' % link.parameter
                return (filetype, url)

            match = PSID_MUSIC.match(link.parameter)
            if match:
                filetype = 'sid'
                url = 'https://modland.ziphoid.com%s' % link.parameter
                return (filetype, url)

        elif link.link_class == 'BaseUrl':
            url = link.parameter
            match = ZXDEMO_MUSIC.match(url)
            if match:
                filetype = match.group(1).lower()
                return (filetype, url)

            match = ABSENCEHQ_PYG_MUSIC.match(url)
            if match:
                filetype = match.group(1).lower()
                return (filetype, url)

            match = MEDIA_DEMOZOO_MUSIC.match(url)
            if match:
                filetype = match.group(1).lower()
                return (filetype if filetype in ('sid', 'sap') else 'openmpt', url)

    else:  # External link
        if link.link_class == 'ModarchiveModule':
            filetype = 'openmpt'
            url = 'https://modarchive.org/jsplayer.php?moduleid=%s' % link.parameter
            return (filetype, url)

    # no match
    return (None, None)


def get_playable_track_data(production):
    # Look in this production's download links for any files that can be played using Cowbell
    tracks = []
    combined_media = Media()
    for link in production.links.all():
        filetype, url = identify_link_as_track(link)

        if filetype:
            player, player_opts, media = PLAYERS_BY_FILETYPE[filetype]
            combined_media += media
            tracks.append({
                'id': link.id,
                'url': url,
                'player': player,
                'playerOpts': player_opts
            })

    return tracks, combined_media
