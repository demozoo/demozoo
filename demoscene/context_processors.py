from django.conf import settings
from search.forms import SearchForm

def global_search_form(request):
	return {'global_search_form': SearchForm()}
