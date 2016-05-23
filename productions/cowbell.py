# Cowbell <https://demozoo.github.io/cowbell/> integration

import re

from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import Media


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
	'openmpt': ('Cowbell.Player.OpenMPT', {
		'pathToLibOpenMPT': staticfiles_storage.url('productions/js/cowbell/libopenmpt.js'),
	}, Media(js=[
		'productions/js/cowbell/cowbell.min.js', 'productions/js/cowbell/openmpt.min.js'
	])),
}

ZXDEMO_MUSIC = re.compile(r'https?://files\.zxdemo\.org/.*\.(stc|pt3|vtx)$', re.I)
ZX_MUSIC = re.compile(r'.*\.(stc|pt3|vtx)$', re.I)
STREAMING_MUSIC = re.compile(r'.*\.(mp3|ogg)$', re.I)
OPENMPT_MUSIC = re.compile(r'.*\.(mod|s3m|xm|it|mptm|stm|nst|m15|stk|wow|ult|669|mtm|med|far|mdl|ams|dsm|amf|okt|dmf|ptm|psm|mt2|dbm|digi|imf|j2b|gdm|umx|plm|mo3|xpk|ppm|mmcmp|sfx|sfx2|mms|pt36)$', re.I)


def identify_link_as_track(link):
	# return a (filetype, url) tuple for this link, or (None, None) if it can't be identified as one

	if link.is_download_link:
		if link.link_class == 'SceneOrgFile':
			match = STREAMING_MUSIC.match(link.parameter)
			if match:
				filetype = match.group(1).lower()
				url = link.link.nl_http_url
				return (filetype, url)

		elif link.link_class == 'ModlandFile':
			match = OPENMPT_MUSIC.match(link.parameter)
			if match:
				filetype = 'openmpt'
				url = 'http://modland.ziphoid.com%s' % link.parameter
				return (filetype, url)

			match = ZX_MUSIC.match(link.parameter)
			if match:
				filetype = match.group(1).lower()
				url = 'http://modland.ziphoid.com%s' % link.parameter
				return (filetype, url)

		elif link.link_class == 'BaseUrl':
			url = link.parameter
			match = ZXDEMO_MUSIC.match(url)
			if match:
				filetype = match.group(1).lower()
				return (filetype, url)

	else:  # External link
		if link.link_class == 'ModarchiveModule':
			filetype = 'openmpt'
			url = 'http://modarchive.org/jsplayer.php?moduleid=%s' % link.parameter
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
