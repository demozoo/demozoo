from django.urls import path

from pages import views as pages_views


urlpatterns = [
    path("<str:slug>/", pages_views.page, {}, "page"),
]
