from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

from demoscene.utils.accounts import is_ip_banned
from search.forms import SearchForm


def global_nav_forms(request):
    return {
        'global_search_form': SearchForm(auto_id="id_global_search-%s"),
        'global_login_form': AuthenticationForm(),
    }


def ajax_base_template(request):
    return {
        'base_template_with_ajax_option': 'minimal_base.html' if request.is_ajax() else 'base.html'
    }


def read_only_mode(request):
    return {
        'site_is_writeable': settings.SITE_IS_WRITEABLE,
        'is_ip_banned': is_ip_banned(request),
    }
