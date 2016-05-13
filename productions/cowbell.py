# Cowbell <https://demozoo.github.io/cowbell/> integration

import re

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
}

ZXDEMO_MUSIC = re.compile(r'https?://files\.zxdemo\.org/.*\.(stc|pt3|vtx)$', re.I)


def get_playable_track_data(production):
	# Look in this production's download links for any files that can be played using Cowbell
	tracks = []
	combined_media = Media()
	for link in production.download_links:
		if link.link_class == 'BaseUrl':
			url = link.parameter
			match = ZXDEMO_MUSIC.match(url)
			if match:
				filetype = match.group(1).lower()
				player, player_opts, media = PLAYERS_BY_FILETYPE[filetype]
				combined_media += media
				tracks.append({
					'id': link.id,
					'url': url,
					'player': player,
					'playerOpts': player_opts
				})
				continue

	return tracks, combined_media
