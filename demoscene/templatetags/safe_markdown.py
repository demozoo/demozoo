from django import template
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_str, force_unicode
import markdown
from scrubber import Scrubber

register = template.Library()

scrubber = Scrubber(autolink=False, nofollow=False) # Scrubber's autolink doesn't handle ftp://
md = markdown.Markdown(extensions=['nl2br', 'autolink'])

def safe_markdown(value, arg=''):
	return mark_safe(
		scrubber.scrub(
			md.convert(value)
		)
	)
safe_markdown.is_safe = True

register.filter(safe_markdown)
