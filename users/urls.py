from django.conf.urls import url
from django.views.generic import RedirectView

from users.views import show

urlpatterns = [
	url(r'^$', RedirectView.as_view(pattern_name='home')),
	url(r'^(\d+)/$', show, {}, 'user'),
]
