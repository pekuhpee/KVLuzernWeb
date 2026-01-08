from django.urls import path

from apps.exams import views

app_name = "exams"

urlpatterns = [
    path("upload", views.upload, name="upload"),
    path("upload/danke", views.upload_thanks, name="upload_thanks"),
    path("upload/batch", views.upload_batch_portal, name="upload_batch"),
    path("d/<int:pk>/download", views.download, name="download"),
    path("api/upload-batches/", views.create_upload_batch, name="create_upload_batch"),
    path(
        "api/upload-batches/<int:batch_id>/files/",
        views.upload_batch_files,
        name="upload_batch_files",
    ),
    path(
        "api/upload-batches/<int:batch_id>/download.zip",
        views.download_upload_batch,
        name="download_upload_batch",
    ),
    path(
        "api/upload-files/<int:file_id>/",
        views.delete_upload_file,
        name="delete_upload_file",
    ),
]
