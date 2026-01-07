import os

from django.db.models import F
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.exams.forms import ContentItemUploadForm
from apps.exams.models import ContentItem


def upload(request):
    if request.method == "POST":
        form = ContentItemUploadForm(request.POST, request.FILES)
        if form.is_valid():
            content_item = form.save(commit=False)
            content_item.status = ContentItem.Status.PENDING
            content_item.download_count = 0
            content_item.save()
            return redirect("exams:upload_thanks")
    else:
        form = ContentItemUploadForm()

    return render(request, "exams/upload.html", {"form": form})


def upload_thanks(request):
    return render(request, "exams/upload_thanks.html")


def download(request, pk):
    content_item = get_object_or_404(
        ContentItem,
        pk=pk,
        status=ContentItem.Status.APPROVED,
    )
    if not content_item.file:
        raise Http404("File not found.")

    storage = content_item.file.storage
    if not storage.exists(content_item.file.name):
        raise Http404("File not found.")

    ContentItem.objects.filter(pk=pk).update(download_count=F("download_count") + 1)

    return FileResponse(
        content_item.file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(content_item.file.name),
    )
