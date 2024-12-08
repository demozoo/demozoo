from django.urls import path

from platforms.views import index, show


urlpatterns = [
    path("", index, {}, "platforms"),
    path("<int:platform_id>/", show, {}, "platform"),
]
