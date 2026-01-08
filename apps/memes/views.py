import hashlib
import uuid

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.memes.forms import MemeUploadForm
from apps.memes.models import Meme, MemeLike

LIKE_RATE_LIMIT = 30
LIKE_RATE_WINDOW_SECONDS = 60 * 60


def _hash_value(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _get_visitor_id(request):
    raw = request.headers.get("X-Visitor-Id", "")
    if not raw:
        return None, JsonResponse({"detail": "X-Visitor-Id header required."}, status=400)
    try:
        return uuid.UUID(raw), None
    except (ValueError, AttributeError):
        return None, JsonResponse({"detail": "X-Visitor-Id must be a valid UUID."}, status=400)


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


@require_GET
def api_memes(request):
    visitor_id, error_response = _get_visitor_id(request)
    if error_response:
        return error_response

    memes = list(Meme.approved.order_by("-created_at"))
    liked_ids = set(
        MemeLike.objects.filter(visitor_id=visitor_id, meme__in=memes).values_list(
            "meme_id", flat=True
        )
    )

    data = [
        {
            "id": meme.id,
            "title": meme.title,
            "image_url": meme.image.url if meme.image else "",
            "like_count": meme.like_count,
            "liked_by_me": meme.id in liked_ids,
        }
        for meme in memes
    ]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_POST
def api_like_meme(request, meme_id):
    visitor_id, error_response = _get_visitor_id(request)
    if error_response:
        return error_response

    if not _check_rate_limit(request):
        return JsonResponse({"detail": "Rate limit exceeded."}, status=429)

    meme = get_object_or_404(Meme, pk=meme_id, status=Meme.Status.APPROVED)
    ip_hash = _hash_value(_get_client_ip(request))
    ua_hash = _hash_value(request.META.get("HTTP_USER_AGENT", ""))

    created = False
    with transaction.atomic():
        try:
            _, created = MemeLike.objects.get_or_create(
                meme=meme,
                visitor_id=visitor_id,
                defaults={"ip_hash": ip_hash, "ua_hash": ua_hash},
            )
        except IntegrityError:
            created = False

        if created:
            Meme.objects.filter(pk=meme.pk).update(like_count=F("like_count") + 1)

    meme.refresh_from_db(fields=["like_count"])
    if created:
        return JsonResponse({"like_count": meme.like_count, "liked": True})
    return JsonResponse({"like_count": meme.like_count, "liked": True, "already_liked": True})
