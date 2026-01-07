from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.exams.models import ContentItem

from .models import *

def index(request):

  context = {
    'segment': 'dashboard',
  }
  return render(request, "dashboard/index.html", context)

@login_required(login_url='/users/signin/')
def starter(request):

  context = {}
  return render(request, "pages/starter.html", context)


def pruefungen(request):

  approved_items = ContentItem.objects.filter(status=ContentItem.Status.APPROVED)

  year = request.GET.get("year")
  content_type = request.GET.get("content_type")
  subject = request.GET.get("subject")
  teacher = request.GET.get("teacher")
  program = request.GET.get("program")
  sort = request.GET.get("sort", "newest")

  items = approved_items
  if year:
    items = items.filter(year=year)
  if content_type:
    items = items.filter(content_type=content_type)
  if subject:
    items = items.filter(subject=subject)
  if teacher:
    items = items.filter(teacher=teacher)
  if program:
    items = items.filter(program=program)

  if sort == "most_downloaded":
    items = items.order_by("-download_count", "-created_at")
  else:
    items = items.order_by("-created_at")

  context = {
    "items": items,
    "year_options": approved_items.exclude(year__isnull=True).values_list("year", flat=True).distinct().order_by("-year"),
    "content_type_options": ContentItem.ContentType.choices,
    "subject_options": approved_items.values_list("subject", flat=True).distinct().order_by("subject"),
    "teacher_options": approved_items.exclude(teacher="").values_list("teacher", flat=True).distinct().order_by("teacher"),
    "program_options": approved_items.exclude(program__isnull=True).values_list("program", flat=True).distinct().order_by("program"),
    "selected_year": year or "",
    "selected_content_type": content_type or "",
    "selected_subject": subject or "",
    "selected_teacher": teacher or "",
    "selected_program": program or "",
    "selected_sort": sort or "newest",
  }
  return render(request, "pages/pruefungen.html", context)
