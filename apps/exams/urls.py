from django.urls import path

from apps.exams import views

app_name = "exams"

urlpatterns = [
    path("upload", views.upload, name="upload"),
    path("upload/danke", views.upload_thanks, name="upload_thanks"),
    path("d/<int:pk>/download", views.download, name="download"),
]
