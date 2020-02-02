from django.conf.urls import url

from awards.views import recommend

urlpatterns = [
    url(r'^(\d+)/recommend/(\d+)/$', recommend, {}, 'awards_recommend'),
]
