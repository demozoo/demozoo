from django.conf import settings
from search.forms import SearchForm

def jquery_include_context_processor(request):
	try:
		use_local_jquery = settings.USE_LOCAL_JQUERY
	except AttributeError:
		use_local_jquery = False
	return {'use_local_jquery': use_local_jquery}

def global_search_form(request):
	return {'global_search_form': SearchForm()}
