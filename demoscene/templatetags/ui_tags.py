from django import template


register = template.Library()


@register.inclusion_tag("shared/button.html")
def button(label=None, icon=None, href=None, lightbox=False, focus=False, disabled=False, variant=None, reverse=False, size=None, level=None, title=None, theme=None):
    return {
        "label": label,
        "icon": icon,
        "href": href,
        "lightbox": lightbox,
        "focus": focus,
        "disabled": disabled,
        "variant": variant,
        "reverse": reverse,
        "size": size,
        "title": title,
        "theme": theme,
        "level": level,
    }
