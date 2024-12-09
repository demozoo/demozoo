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


@register.inclusion_tag("tags/action_button.html")
def action_button(
    label=None, icon=None, url=None, classname=None, lightbox=False, focus_empty=False, title=None, nofollow=False
):
    return {
        "tag": "a" if url else "button",
        "url": reverse(url) if (url and not url.startswith("/")) else url,
        "label": label,
        "icon": icon,
        "classname": classname,
        "lightbox": lightbox,
        "focus_empty": focus_empty,
        "title": title,
        "nofollow": nofollow,
    }
