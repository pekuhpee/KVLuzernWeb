import hashlib
import secrets
from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from apps.ranking.models import RankingCategory, RankingVote, Teacher

TOKEN_COOKIE_NAME = "kvls_vote_token"
TOKEN_MAX_AGE = 60 * 60 * 24 * 365


def _get_or_create_token(request):
    token = request.COOKIES.get(TOKEN_COOKIE_NAME)
    created = False
    if not token:
        token = secrets.token_urlsafe(32)
        created = True
    return token, created

def _hash_token(token):
    return hashlib.sha256(f"{token}{settings.SECRET_KEY}".encode("utf-8")).hexdigest()

def _apply_token_cookie(response, token, created):
    if created:
        response.set_cookie(
            TOKEN_COOKIE_NAME, token, max_age=TOKEN_MAX_AGE, httponly=True, samesite="Lax"
        )
    return response

def _next_category_for_token(token_hash):
    return (
        RankingCategory.objects.exclude(rankingvote__token_hash=token_hash)
        .order_by("order", "title")
        .first()
    )


def start(request):
    token, created = _get_or_create_token(request)
    token_hash = _hash_token(token)
    categories = RankingCategory.objects.order_by("order", "title")
    if not categories.exists():
        response = render(request, "ranking/index.html")
        return _apply_token_cookie(response, token, created)
    category = _next_category_for_token(token_hash)
    if not category:
        response = redirect("ranking:results")
        return _apply_token_cookie(response, token, created)
    teachers = Teacher.objects.filter(active=True).order_by("name")
    response = render(
        request, "ranking/index.html", {"category": category, "teachers": teachers}
    )
    return _apply_token_cookie(response, token, created)

def vote(request):
    if request.method != "POST":
        return redirect("ranking:start")
    token, created = _get_or_create_token(request)
    token_hash = _hash_token(token)
    category = get_object_or_404(RankingCategory, id=request.POST.get("category_id"))
    teacher = get_object_or_404(Teacher, id=request.POST.get("teacher_id"), active=True)
    if RankingVote.objects.filter(category=category, token_hash=token_hash).exists():
        next_category = _next_category_for_token(token_hash)
        response = render(
            request,
            "ranking/index.html",
            {"category": category, "already_voted": True, "next_category": next_category},
        )
        return _apply_token_cookie(response, token, created)
    RankingVote.objects.create(category=category, teacher=teacher, token_hash=token_hash)
    response = redirect("ranking:start") if _next_category_for_token(token_hash) else redirect("ranking:results")
    return _apply_token_cookie(response, token, created)

def results(request):
    categories = list(RankingCategory.objects.order_by("order", "title"))
    teachers = list(Teacher.objects.order_by("name"))
    if not categories or not teachers:
        return render(request, "ranking/results.html")
    vote_counts = {
        (row["category_id"], row["teacher_id"]): row["total"]
        for row in RankingVote.objects.values("category_id", "teacher_id").annotate(
            total=Count("id")
        )
    }
    category_results = []
    for category in categories:
        rows = []
        total_votes = 0
        max_votes = 0
        for teacher in teachers:
            count = vote_counts.get((category.id, teacher.id), 0)
            total_votes += count
            max_votes = max(max_votes, count)
            rows.append({"teacher": teacher, "count": count})
        for row in rows:
            row["percent"] = (row["count"] / max_votes) * 100 if max_votes else 0
        category_results.append({"category": category, "rows": rows, "total_votes": total_votes})
    return render(request, "ranking/results.html", {"category_results": category_results})
