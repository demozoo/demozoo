import markdown
from bleach.sanitizer import Cleaner
from django import template
from django.utils.safestring import mark_safe

from common.utils.markdown import AutoLinkExtension


register = template.Library()


cleaner = Cleaner(
    tags={
        "a",
        "b",
        "blockquote",
        "br",
        "center",
        "code",
        "del",
        "div",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "img",
        "i",
        "li",
        "ol",
        "pre",
        "p",
        "strike",
        "strong",
        "sup",
        "sub",
        "ul",
    },
    attributes={
        "a": ("href", "name", "title", "id", "rel"),
        "div": ("class",),
        "img": ("src", "width", "height", "alt"),
        "li": ("id",),
        "sup": ("id",),
    },
    strip=True,
    protocols={"http", "https", "mailto", "ftp", "tel"},
)
autolink = AutoLinkExtension()
md = markdown.Markdown(extensions=["footnotes", "nl2br", autolink])


@register.filter(is_safe=True)
def safe_markdown(value, arg=""):
    return mark_safe(cleaner.clean(md.reset().convert(value)))
