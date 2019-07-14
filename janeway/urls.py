from django.conf.urls import url
from django.views.generic import RedirectView

from janeway import views

urlpatterns = [
	url(r'^$', RedirectView.as_view(url='/janeway/authors/')),
	url(r'^authors/$', views.authors, {}, 'janeway_authors'),
	url(r'^authors/(\d+)/$', views.match_author, {}, 'janeway_match_author'),
	url(r'^production-link/$', views.production_link, {}, 'janeway_production_link'),
	url(r'^production-unlink/$', views.production_unlink, {}, 'janeway_production_unlink'),
]
