from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.exams.models import ContentItem, MetaCategory, MetaOption
from apps.ranking.models import Teacher

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
  content_type = request.GET.get("type")
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

  meta_labels = {category.key: category.label for category in MetaCategory.objects.filter(is_active=True).order_by("sort_order", "label")}

  context = {
    "items": items,
    "year_options": MetaOption.objects.filter(category__key="year", category__is_active=True, is_active=True).order_by("sort_order", "label"),
    "content_type_options": MetaOption.objects.filter(category__key="type", category__is_active=True, is_active=True).order_by("sort_order", "label"),
    "subject_options": MetaOption.objects.filter(category__key="subject", category__is_active=True, is_active=True).order_by("sort_order", "label"),
    "teacher_options": Teacher.objects.order_by("-active", "name"),
    "program_options": MetaOption.objects.filter(category__key="program", category__is_active=True, is_active=True).order_by("sort_order", "label"),
    "selected_year": year or "",
    "selected_content_type": content_type or "",
    "selected_subject": subject or "",
    "selected_teacher": teacher or "",
    "selected_program": program or "",
    "selected_sort": sort or "newest",
    "meta_labels": meta_labels,
  }
  return render(request, "pages/pruefungen.html", context)
