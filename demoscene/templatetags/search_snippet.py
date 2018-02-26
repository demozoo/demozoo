from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
@stringfilter
def search_snippet(text, resultset):
	output = highlight_snippet(resultset, text)
	if output:
		return mark_safe('<p class="snippet">' + output + '</p>')
	else:
		return ''


def highlight_snippet(resultset, text, tag="strong"):
	terms = tuple(resultset.get_parsed_query_terms())
	if resultset._stemming_lang:
		stem = resultset._indexer.get_stemmer(resultset._stemming_lang)
	else:
		stem = lambda a: a

	words = text.split()
	for (i, word) in enumerate(words):
		if stem(re.sub(r'\W', '', word.lower())) in terms:
			start = max(0, i-8)
			snippet = words[start:start+25]
			for (i, word) in enumerate(snippet):
				if stem(re.sub(r'\W', '', word.lower())) in terms:
					snippet[i] = '<%(tag)s>%(word)s</%(tag)s>' % {"tag": tag, "word": word}
			return '...' + ' '.join(snippet) + '...'
