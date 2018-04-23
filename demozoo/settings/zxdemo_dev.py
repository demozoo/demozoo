from .dev import *

TEMPLATES[0]['OPTIONS']['context_processors'] = [
	'django.contrib.auth.context_processors.auth',
	'django.template.context_processors.debug',
	'django.template.context_processors.i18n',
	'django.template.context_processors.media',
	'django.template.context_processors.static',
	'django.template.context_processors.tz',
	'django.contrib.messages.context_processors.messages',

	'django.template.context_processors.request',
	'zxdemo.context_processors.zxdemo_context',
]

ROOT_URLCONF = 'zxdemo.urls'

ZXDEMO_PLATFORM_IDS = [2]
