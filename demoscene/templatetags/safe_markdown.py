from __future__ import absolute_import, unicode_literals

from django import template
from django.utils.safestring import mark_safe
import markdown
from html_sanitizer import Sanitizer

register = template.Library()


def sanitize_href(href):
    """
    Verify that a given href is benign and allowed.
    This is a stupid check, which probably should be much more elaborate
    to be safe.
    """
    if href.startswith(("/", "mailto:", "http:", "https:", "#", "tel:", "ftp:")):
        return href
    return "#"


sanitizer = Sanitizer({
    'tags': (
        'a', 'b', 'blockquote', 'br', 'center', 'code', 'del', 'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'i', 'li',
        'ol', 'pre', 'p', 'strike', 'strong', 'sup', 'sub', 'ul',
    ),
    'attributes': {
        "a": ("href", "name", "title", "id", "rel"),
        "img": ("src", "width", "height", "alt"),
    },
    'element_preprocessors': [],
    'sanitize_href': sanitize_href,
})
md = markdown.Markdown(extensions=['nl2br', 'autolink'])

@register.filter(is_safe=True)
def safe_markdown(value, arg=''):
    return mark_safe(
        sanitizer.sanitize(
            md.reset().convert(value)
        )
    )
