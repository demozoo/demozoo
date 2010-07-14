from django import template
import markdown2
from scrubber import Scrubber
register = template.Library()

scrubber = Scrubber()

def safe_markdown(value, arg=''):
	return scrubber.scrub(markdown2.markdown(value))
safe_markdown.is_safe = True

register.filter(safe_markdown)
