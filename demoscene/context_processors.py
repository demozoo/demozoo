from django.conf import settings
from search.forms import SearchForm
from django.contrib.auth.forms import AuthenticationForm

def global_nav_forms(request):
	return {
		'global_search_form': SearchForm(),
		'global_login_form': AuthenticationForm(),
	}
