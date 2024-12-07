from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def urlsub(context, **params_to_replace):
    params = context["request"].GET.copy()
    for k, v in params_to_replace.items():
        # can't use params.update here, because with QueryDict that appends to the list
        # for each param rather than updating it. Grr.
        params[k] = v

    param_string = params.urlencode()

    if param_string:
        return "?" + param_string
    else:
        return ""
