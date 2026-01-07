from django.shortcuts import redirect, render

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
