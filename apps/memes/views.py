import uuid

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.memes.forms import MemeUploadForm
from apps.memes.models import Meme, MemeLike

LIKE_RATE_LIMIT = 30
LIKE_RATE_WINDOW_SECONDS = 60 * 60


def _get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _get_anon_id(request):
    raw = request.COOKIES.get("anon_id")
    if raw:
        try:
            return uuid.UUID(raw), False
        except (ValueError, TypeError):
            pass
    return uuid.uuid4(), True


def _check_rate_limit(request):
    ip = _get_client_ip(request) or "unknown"
    cache_key = f"memes_like_rate:{ip}"
    try:
        if cache.add(cache_key, 1, timeout=LIKE_RATE_WINDOW_SECONDS):
            return True
        current = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=LIKE_RATE_WINDOW_SECONDS)
        current = 1
    return current <= LIKE_RATE_LIMIT


def index(request):
    anon_id, needs_cookie = _get_anon_id(request)
    memes = Meme.approved.order_by("-created_at")
    liked_ids = set(
        MemeLike.objects.filter(anon_id=anon_id, meme__in=memes).values_list(
            "meme_id", flat=True
        )
    )
    response = render(
        request,
        "memes/index.html",
        {"memes": memes, "liked_ids": liked_ids},
    )
    if needs_cookie:
        response.set_cookie(
            "anon_id", str(anon_id), max_age=60 * 60 * 24 * 365, samesite="Lax"
        )
    return response


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


@require_GET
def api_memes(request):
    anon_id, needs_cookie = _get_anon_id(request)

    memes = list(Meme.approved.order_by("-created_at"))
    liked_ids = set(
        MemeLike.objects.filter(anon_id=anon_id, meme__in=memes).values_list(
            "meme_id", flat=True
        )
    )

    data = [
        {
            "id": meme.id,
            "title": meme.title,
            "image_url": meme.image_url,
            "like_count": meme.like_count,
            "liked_by_me": meme.id in liked_ids,
        }
        for meme in memes
    ]
    response = JsonResponse(data, safe=False)
    if needs_cookie:
        response.set_cookie(
            "anon_id", str(anon_id), max_age=60 * 60 * 24 * 365, samesite="Lax"
        )
    return response


@require_POST
def api_like_meme(request, meme_id):
    anon_id, needs_cookie = _get_anon_id(request)

    if not _check_rate_limit(request):
        return JsonResponse({"detail": "Rate limit exceeded."}, status=429)

    meme = get_object_or_404(Meme, pk=meme_id, status=Meme.Status.APPROVED)

    created = False
    with transaction.atomic():
        try:
            _, created = MemeLike.objects.get_or_create(
                meme=meme,
                anon_id=anon_id,
            )
        except IntegrityError:
            created = False

        if created:
            Meme.objects.filter(pk=meme.pk).update(like_count=F("like_count") + 1)

    meme.refresh_from_db(fields=["like_count"])
    response = JsonResponse(
        {"like_count": meme.like_count, "liked": True, "already_liked": not created}
    )
    if needs_cookie:
        response.set_cookie(
            "anon_id", str(anon_id), max_age=60 * 60 * 24 * 365, samesite="Lax"
        )
    return response
