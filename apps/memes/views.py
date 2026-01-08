from django.shortcuts import redirect, render

from apps.memes.forms import MemeUploadForm
from apps.memes.models import Meme


def index(request):
    memes = Meme.objects.filter(status=Meme.Status.APPROVED).order_by("-created_at")
    return render(request, "memes/index.html", {"memes": memes})


def upload(request):
    if request.method == "POST":
        form = MemeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            meme = form.save(commit=False)
            meme.status = Meme.Status.PENDING
            meme.save()
            return redirect("memes:thanks")
    else:
        form = MemeUploadForm()

    return render(request, "memes/upload.html", {"form": form})


def thanks(request):
    return render(request, "memes/thanks.html")
