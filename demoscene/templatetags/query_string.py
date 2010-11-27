from django import template
from django.utils.safestring import mark_safe
import urllib

register = template.Library()

@register.tag
def query_string(parser, token):
    """
    Allows you too manipulate the query string of a page by adding and removing keywords.
    If a given value is a context variable it will resolve it.
    Based on similiar snippet by user "dnordberg".
    
    requires you to add:
    
    TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    )
    
    to your django settings. 
    
    Usage:
    http://www.url.com/{% query_string "param_to_add=value, param_to_add=value" "param_to_remove, params_to_remove" %}
    
    Example:
    http://www.url.com/{% query_string "" "filter" %}filter={{new_filter}}
    http://www.url.com/{% query_string "page=page_obj.number" "sort" %} 
    
    """
    try:
        tag_name, add_string,remove_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires two arguments" % token.contents.split()[0]
    if not (add_string[0] == add_string[-1] and add_string[0] in ('"', "'")) or not (remove_string[0] == remove_string[-1] and remove_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    
    add = string_to_dict(add_string[1:-1])
    remove = string_to_list(remove_string[1:-1])
    
    return QueryStringNode(add,remove)

class QueryStringNode(template.Node):
    def __init__(self, add,remove):
        self.add = add
        self.remove = remove
        
    def render(self, context):
        p = {}
        for k, v in context["request"].GET.items():
            p[k]=v
        return get_query_string(p,self.add,self.remove,context)

def get_query_string(p, new_params, remove, context):
    """
    Add and remove query parameters. From `django.contrib.admin`.
    """
    for r in remove:
        for k in p.keys():
            if k.startswith(r):
                del p[k]
    for k, v in new_params.items():
        if k in p and v is None:
            del p[k]
        elif v is not None:
            p[k] = v
            
    for k, v in p.items():
        try:
            p[k] = template.Variable(v).resolve(context)
        except:
            p[k]=v
                
    return mark_safe('?' + '&amp;'.join([u'%s=%s' % (urllib.quote_plus(str(k)), urllib.quote_plus(str(v))) for k, v in p.items()]))

# Taken from lib/utils.py   
def string_to_dict(string):
    kwargs = {}
    
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            kw, val = arg.split('=', 1)
            kwargs[kw] = val
    return kwargs

def string_to_list(string):
    args = []
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            args.append(arg)
    return args