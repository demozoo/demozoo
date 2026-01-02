import re

from django.forms import Media
from django.templatetags.static import static


# Cowbell <https://demozoo.github.io/cowbell/> integration

PLAYERS_BY_FILETYPE = {
    "stc": (
        "Cowbell.Player.ZXSTC",
        {},
        Media(
            js=[
                "productions/js/cowbell/cowbell.min.js",
                "productions/js/cowbell/ay_chip.min.js",
                "productions/js/cowbell/zx.min.js",
            ]
        ),
    ),
    "pt3": (
        "Cowbell.Player.ZXPT3",
        {},
        Media(
            js=[
                "productions/js/cowbell/cowbell.min.js",
                "productions/js/cowbell/ay_chip.min.js",
                "productions/js/cowbell/zx.min.js",
            ]
        ),
    ),
    "sqt": (
        "Cowbell.Player.ZXSQT",
        {},
        Media(
            js=[
                "productions/js/cowbell/cowbell.min.js",
                "productions/js/cowbell/ay_chip.min.js",
                "productions/js/cowbell/zx.min.js",
            ]
        ),
    ),
    "pyg": (  # PSG format configured with YM / Atari ST parameters
        "Cowbell.Player.PSG",
        {"ayFrequency": 2000000, "ayMode": "YM"},
        Media(
            js=[
                "productions/js/cowbell/cowbell.min.js",
                "productions/js/cowbell/ay_chip.min.js",
            ]
        ),
    ),
    "vtx": (
        "Cowbell.Player.VTX",
        {},
        Media(
            js=[
                "productions/js/cowbell/cowbell.min.js",
                "productions/js/cowbell/ay_chip.min.js",
                "productions/js/cowbell/vtx.min.js",
            ]
        ),
    ),
    "mp3": ("Cowbell.Player.Audio", {}, Media(js=["productions/js/cowbell/cowbell.min.js"])),
    "ogg": ("Cowbell.Player.Audio", {}, Media(js=["productions/js/cowbell/cowbell.min.js"])),
    "wav": ("Cowbell.Player.Audio", {}, Media(js=["productions/js/cowbell/cowbell.min.js"])),
    "opus": ("Cowbell.Player.Audio", {}, Media(js=["productions/js/cowbell/cowbell.min.js"])),
    "flac": ("Cowbell.Player.Audio", {}, Media(js=["productions/js/cowbell/cowbell.min.js"])),
    "openmpt": (
        "Cowbell.Player.OpenMPT",
        {
            "pathToLibOpenMPT": static("productions/js/cowbell/libopenmpt.js"),
        },
        Media(js=["productions/js/cowbell/cowbell.min.js", "productions/js/cowbell/openmpt.min.js"]),
    ),
    "sndh": (
        "Cowbell.Player.PSGPlay",
        {},
        Media(js=["productions/js/cowbell/cowbell.min.js", "productions/js/cowbell/psgplay.min.js"]),
    ),
    "sid": (
        "Cowbell.Player.JSSID",
        {},
        Media(js=["productions/js/cowbell/cowbell.min.js", "productions/js/cowbell/jssid.min.js"]),
    ),
    "sap": (
        "Cowbell.Player.ASAP",
        {},
        Media(js=["productions/js/cowbell/cowbell.min.js", "productions/js/cowbell/asap.min.js"]),
    ),
}

ZXDEMO_MUSIC = re.compile(r"https://files\.zxdemo\.org/.*\.(stc|pt3|vtx|sqt|pyg|sndh)$", re.I)
ABSENCEHQ_PYG_MUSIC = re.compile(r"https://absencehq.de/atari/.*\.(pyg)$", re.I)
ASMA_SAP_MUSIC = re.compile(r"https://asma.atari.org/asma/.*\.(sap)(\#\w*)?$", re.I)
MODLAND_NON_OPENMPT_MUSIC = re.compile(r".*\.(stc|pt3|vtx|sqt|sndh)$", re.I)
STREAMING_MUSIC = re.compile(r".*\.(mp3|ogg|wav|opus|flac)$", re.I)
OPENMPT_MUSIC = re.compile(
    r".*\.(mod|s3m|xm|it|mptm|stm|nst|m15|stk|wow|ult|669|mtm|med|far|mdl|ams|dsm|amf|okt|dmf|ptm"
    r"|psm|mt2|dbm|digi|imf|j2b|gdm|umx|plm|mo3|xpk|ppm|mmcmp|sfx|sfx2|mms|pt36|nt|ft|fmt|dsym"
    r"|symmod|667|gtk|gt2|xmf|stx|mus|puma|ftm|fc|fc13|fc14|smod|gmc|cba|rtm|ims|etx|unic|tcb)$",
    re.I,
)
# Recognise .sid and .psid files on Modland as SID files, UNLESS they are .sid files in
# /pub/modules/SidMon 1/ which are a totally different Amiga format. Yay consistency.
# SID files on Modland mostly have the extension .psid to distinguish them from Amiga Sidmon tracker files
MODLAND_SID_MUSIC = re.compile(r".*\.(sid|psid)$", re.I)
MODLAND_SIDMON_MUSIC = re.compile(r"/pub/modules/sidmon( |%20)1/.*\.sid$", re.I)

NONSTANDARD_MODLAND_EXTENSIONS = re.compile(r".*\.(mmd0|mmd1|mmd2|mmd3)", re.I)

# stuff mirrored on media.demozoo.org/music
MEDIA_DEMOZOO_MUSIC = re.compile(r"https://media\.demozoo\.org/music/.*\.(mod|s3m|xm|it|sid|sap|sndh)$", re.I)


def identify_link_as_track(link):
    # return a (filetype, url) tuple for this link, or (None, None) if it can't be identified as one

    if link.is_download_link:
        if link.link_class == "SceneOrgFile":
            match = STREAMING_MUSIC.match(link.parameter)
            if match:
                filetype = match.group(1).lower()
                url = link.link.nl_https_url
                return (filetype, url)

        elif link.link_class == "ModlandFile":
            if OPENMPT_MUSIC.match(link.parameter) or NONSTANDARD_MODLAND_EXTENSIONS.match(link.parameter):
                filetype = "openmpt"
                url = "https://modland.ziphoid.com%s" % link.parameter
                return (filetype, url)

            match = MODLAND_NON_OPENMPT_MUSIC.match(link.parameter)
            if match:
                filetype = match.group(1).lower()
                url = "https://modland.ziphoid.com%s" % link.parameter
                return (filetype, url)

            if MODLAND_SID_MUSIC.match(link.parameter) and not MODLAND_SIDMON_MUSIC.match(link.parameter):
                filetype = "sid"
                url = "https://modland.ziphoid.com%s" % link.parameter
                return (filetype, url)

        elif link.link_class == "BaseUrl":
            url = link.parameter
            if match := ZXDEMO_MUSIC.match(url) or ABSENCEHQ_PYG_MUSIC.match(url) or ASMA_SAP_MUSIC.match(url):
                filetype = match.group(1).lower()
                return (filetype, url)

            elif match := MEDIA_DEMOZOO_MUSIC.match(url):
                filetype = match.group(1).lower()
                return (filetype if filetype in ("sid", "sap", "sndh") else "openmpt", url)

    else:  # External link
        if link.link_class == "ModarchiveModule":
            filetype = "openmpt"
            url = "https://modarchive.org/jsplayer.php?moduleid=%s" % link.parameter
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
            tracks.append({"id": link.id, "url": url, "player": player, "playerOpts": player_opts})

    return tracks, combined_media
