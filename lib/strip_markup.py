import markdown
from django.utils.html import strip_tags

md = markdown.Markdown(extensions=['nl2br'])

def strip_markup(str):
	return strip_tags(md.convert(str))
