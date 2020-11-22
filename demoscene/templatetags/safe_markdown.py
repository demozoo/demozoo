from __future__ import absolute_import, unicode_literals

from django import template
from django.utils.safestring import mark_safe

from bleach.sanitizer import Cleaner
import markdown
from mdx_autolink import AutoLinkExtension

register = template.Library()


cleaner = Cleaner(
    tags=[
        'a', 'b', 'blockquote', 'br', 'center', 'code', 'del', 'em',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'i', 'li',
        'ol', 'pre', 'p', 'strike', 'strong', 'sup', 'sub', 'ul',
    ],
    attributes={
        "a": ("href", "name", "title", "id", "rel"),
        "img": ("src", "width", "height", "alt"),
    },
    strip=True,
    protocols=['http', 'https', 'mailto', 'ftp', 'tel'],
)
autolink = AutoLinkExtension()
md = markdown.Markdown(extensions=['nl2br', autolink])

@register.filter(is_safe=True)
def safe_markdown(value, arg=''):
    return mark_safe(
        cleaner.clean(
            md.reset().convert(value)
        )
    )
