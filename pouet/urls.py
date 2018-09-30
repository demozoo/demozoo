from django.conf.urls import url
from django.views.generic import RedirectView

from pouet import views

urlpatterns = [
	url(r'^$', RedirectView.as_view(url='/pouet/groups/')),
	url(r'^groups/$', views.groups, {}, 'pouet_groups'),
	url(r'^groups/(\d+)/$', views.match_group, {}, 'pouet_match_group'),
]
