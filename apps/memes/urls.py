from django.urls import path

from apps.memes import views

app_name = "memes"

urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.upload, name="upload"),
    path("danke/", views.thanks, name="thanks"),
]
