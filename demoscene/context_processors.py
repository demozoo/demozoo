from search.forms import SearchForm
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings


def global_nav_forms(request):
	return {
		'global_search_form': SearchForm(),
		'global_login_form': AuthenticationForm(),
	}


def ajax_base_template(request):
	return {
		'base_template_with_ajax_option': 'minimal_base.html' if request.is_ajax() else 'base.html'
	}


def read_only_mode(request):
	return {
		'site_is_writeable': settings.SITE_IS_WRITEABLE
	}
