import re
import unicodedata

from django.utils.safestring import mark_safe

def slugify_tag(value):
	"""
	A version of django.utils.text.slugify that lets '.' characters through.
	"""
	value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
	value = re.sub('[^\w\s\.-]', '', value).strip().lower()
	return mark_safe(re.sub('[-\s]+', '-', value))


def generate_sort_key(s):
	# strip accents
	s = ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))

	# replace punctuation with spaces
	s = ''.join((' ' if unicodedata.category(c)[0] == 'P' else c) for c in s)

	# condense multiple spaces to single space; strip leading/trailing space; downcase
	s = re.sub(r'\s+', ' ', s).strip().lower()

	# pad numbers with leading zeros
	s = re.sub(r'\d+', lambda m: '%09d' % (int(m.group(0))), s)

	# move "the" / "a" / "an" to the end
	s = re.sub(r'^(the|a|an)\s+(.*)$', r'\2 \1', s)

	return s
