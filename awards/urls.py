from django.conf.urls import url

from awards.views import recommend, user_recommendations, remove_recommendation

urlpatterns = [
    url(r'^(\d+)/recommend/(\d+)/$', recommend, {}, 'awards_recommend'),
    url(r'^(\d+)/$', user_recommendations, {}, 'awards_user_recommendations'),
    url(r'^remove_recommendation/(\d+)/$', remove_recommendation, {}, 'awards_remove_recommendation'),
]
