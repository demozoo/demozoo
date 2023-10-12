from django import template


register = template.Library()


@register.inclusion_tag("shared/button.html")
def button(label=None, icon=None, href=None, disabled=False, variant=None, reverse=False, size=None, level=None):
    return {
        "label": label,
        "icon": icon,
        "href": href,
        "disabled": disabled,
        "variant": variant,
        "reverse": reverse,
        "size": size,
        "level": level,
    }
