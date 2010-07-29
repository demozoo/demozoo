from django.conf.urls.defaults import *
from haystack.forms import SearchForm
from search.views import AutofollowingSearchView

# Without threading...
urlpatterns = patterns('haystack.views',
    url(r'^$', AutofollowingSearchView(
        form_class=SearchForm
    ), name='search'),
)
