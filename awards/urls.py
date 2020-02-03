from django.conf.urls import url

from awards.views import recommend, user_recommendations

urlpatterns = [
    url(r'^(\d+)/recommend/(\d+)/$', recommend, {}, 'awards_recommend'),
    url(r'^(\d+)/$', user_recommendations, {}, 'awards_user_recommendations'),
]
