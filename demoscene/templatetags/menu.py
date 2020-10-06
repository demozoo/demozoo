from __future__ import absolute_import, unicode_literals

from django import template
from django.core import urlresolvers
from django.db.models import Q
from django.urls import reverse

from awards.models import Event

register = template.Library()

@register.tag(name="nav_active")
def do_nav_active(parser, token):
    section_names = token.split_contents()[1:]
    return NavActiveNode(section_names)

class NavActiveNode(template.Node):
    def __init__(self, section_names):
        self.section_names = section_names
        self.request_var = template.Variable('request')
        self.menu_section_var = template.Variable('menu_section')
    def render(self, context):
        # grab current section name from 'menu_section' variable, falling back on last part of module name if not set
        try:
            current_section_name = self.menu_section_var.resolve(context)
        except template.VariableDoesNotExist:
            try:
                request = self.request_var.resolve(context)
                func, args, kwargs = urlresolvers.resolve(request.path)
                current_section_name = func.__module__.split('.')[-1]
            except (template.VariableDoesNotExist, urlresolvers.Resolver404):
                return ""
        
        if current_section_name in self.section_names:
            return "active"
        else:
            return ""


@register.inclusion_tag('shared/user_menu.html', takes_context=True)
def user_menu(context):
    user = context['request'].user

    menu_items = [
        (reverse('account_change_password'), "Change password"),
    ]

    for event in Event.active_for_user(user):
        menu_items.append(
            (reverse('awards_user_recommendations', args=(event.slug,)), event.name),
        )

    menu_items.append(
        (reverse('user', args=(user.id, )), "Activity"),
    )

    if user.is_staff:
        menu_items.append(
            (reverse('maintenance:index'), "Maintenance"),
        )

    menu_items.append(
        (reverse('log_out'), "Log out"),
    )

    return {
        'menu_items': menu_items,
    }
