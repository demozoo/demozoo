from django.conf.urls import url

from pages import views as pages_views

urlpatterns = [
	url(r'^(.+)/$', pages_views.page, {}, 'page'),
]
