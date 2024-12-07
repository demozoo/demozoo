from django import template


register = template.Library()


@register.inclusion_tag("tags/icon.html")
def icon(icon):
    return {"icon": icon}


@register.inclusion_tag("tags/location_flag.html")
def location_flag(obj):
    # obj = any model instance inheriting from LocationMixin
    return {"obj": obj}
