from haystack.views import SearchView
from django.http import HttpResponseRedirect

class AutofollowingSearchView(SearchView):
	def __name__(self):
		return "AutofollowingSearchView"

	def create_response(self):
		"""
		Generates the actual HttpResponse to send back to the user.
		"""
		if self.results and len(self.results) == 1:
			return HttpResponseRedirect(self.results[0].object.get_absolute_url())
		else:
			return super(AutofollowingSearchView, self).create_response()
