from django import template
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_str, force_unicode
import markdown2
from scrubber import Scrubber
from github_flavored_markdown import gfm

register = template.Library()

scrubber = Scrubber()

def safe_markdown(value, arg=''):
	return mark_safe(
		scrubber.scrub(
			markdown2.markdown(gfm(smart_str(value)))
		)
	)
safe_markdown.is_safe = True

register.filter(safe_markdown)
