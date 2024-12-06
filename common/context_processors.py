from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm

from common.utils.ajax import request_is_ajax
from search.forms import SearchForm
from users.utils import is_login_banned


def global_nav_forms(request):
    return {
        'global_search_form': SearchForm(auto_id="id_global_search-%s"),
        'global_login_form': AuthenticationForm(),
    }


def ajax_base_template(request):
    return {
        'base_template_with_ajax_option': 'minimal_base.html' if request_is_ajax(request) else 'base.html'
    }


def read_only_mode(request):
    return {
        'site_is_writeable': settings.SITE_IS_WRITEABLE,
        'is_ip_banned': is_login_banned(request),
    }
