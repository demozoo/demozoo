import markdown2
from github_flavored_markdown import gfm
from django.utils.html import strip_tags

def strip_markup(str):
	return strip_tags(markdown2.markdown(gfm(str)))
