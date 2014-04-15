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
