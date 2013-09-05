from django.conf import settings
from search.forms import SearchForm
from django.contrib.auth.forms import AuthenticationForm


def global_nav_forms(request):
	return {
		'global_search_form': SearchForm(),
		'global_login_form': AuthenticationForm(),
	}


def read_only_mode(request):
	return {
		'site_is_writeable': settings.SITE_IS_WRITEABLE
	}
