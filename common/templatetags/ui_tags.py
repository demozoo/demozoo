import re

from django import template
from django.urls import reverse


register = template.Library()


@register.inclusion_tag("tags/icon.html")
def icon(icon):
    return {"icon": icon}


@register.inclusion_tag("tags/location_flag.html")
def location_flag(obj):
    # obj = any model instance inheriting from LocationMixin
    return {"obj": obj}


def thumbnail_params_for_size(screenshot, target_width, target_height):
    width, height = screenshot.thumb_dimensions_to_fit(target_width, target_height)

    return {
        "url": screenshot.thumbnail_url,
        "width": width,
        "height": height,
        "natural_width": screenshot.thumbnail_width or 1,
        "natural_height": screenshot.thumbnail_height or 1,
    }


@register.inclusion_tag("tags/thumbnail.html")
def thumbnail(screenshot):
    return thumbnail_params_for_size(screenshot, 133, 100)


@register.inclusion_tag("tags/microthumb.html")
def microthumb(screenshot):
    return thumbnail_params_for_size(screenshot, 48, 36)


@register.inclusion_tag("tags/thumbnail.html")
def megathumb(screenshot):
    width, height = screenshot.thumb_dimensions_to_fit(400, 300)
    return {
        "url": screenshot.standard_url,
        "width": width,
        "height": height,
    }


# Values that are passed directly from attributes of the {% action_button %} or {% icon_button %} tag
# to the template context
COMMON_BUTTON_KWARGS = ["icon", "classname", "lightbox", "focus_empty", "title", "nofollow", "label", "attrs"]


@register.inclusion_tag("tags/action_button.html")
def action_button(url=None, **kwargs):
    context = {key: kwargs.get(key) for key in COMMON_BUTTON_KWARGS}
    context.update(
        {
            "tag": "a" if url else "button",
            "url": reverse(url) if (url and not url.startswith("/")) else url,
        }
    )
    return context


@register.inclusion_tag("tags/icon_button.html")
def icon_button(url=None, **kwargs):
    context = {key: kwargs.get(key) for key in COMMON_BUTTON_KWARGS}
    context.update(
        {
            "tag": "a" if url else "button",
            "url": reverse(url) if (url and not url.startswith("/")) else url,
        }
    )
    return context


# shortcut for {% icon_button %} with icon defaulting to "edit"
@register.inclusion_tag("tags/icon_button.html")
def edit_button(icon="edit", **kwargs):
    return icon_button(icon=icon, **kwargs)


# replace (s)ftp:// urls with clickable link
@register.filter(is_safe=True)
def urlize_ftp(text):
    if "ftp://" in text:
        return re.sub(r'((s?ftp):\/\/(?:([^@\s]+)@)?([^\?\s\:]+)(?:\:([0-9]+))?(?:\?(.+))?)',
                      r'<a href="\1">\1</a>',
                      text)
    return text
