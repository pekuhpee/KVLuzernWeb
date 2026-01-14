from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.exams.models import MetaCategory, MetaOption, UploadBatch
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

  approved_batches = UploadBatch.objects.filter(status=UploadBatch.Status.APPROVED)

  year = request.GET.get("year")
  content_type = request.GET.get("type")
  subject = request.GET.get("subject")
  teacher = request.GET.get("teacher")
  program = request.GET.get("program")
  sort = request.GET.get("sort", "newest")

  batches = approved_batches
  if year:
    batches = batches.filter(year_option__value_key=year)
  if content_type:
    batches = batches.filter(content_type=content_type)
  if subject:
    batches = batches.filter(subject_option__value_key=subject)
  if teacher:
    batches = batches.filter(teacher__name=teacher)
  if program:
    batches = batches.filter(program_option__value_key=program)

  sort_mapping = {
    "newest": ("-created_at",),
    "downloads": ("-download_count", "-created_at"),
  }
  ordering = sort_mapping.get(sort, sort_mapping["newest"])
  batches = batches.order_by(*ordering)

  meta_labels = {category.key: category.label for category in MetaCategory.objects.filter(is_active=True).order_by("sort_order", "label")}

  context = {
    "batches": batches.select_related(
      "type_option",
      "year_option",
      "subject_option",
      "program_option",
      "teacher",
    ).prefetch_related("files"),
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
    "selected_sort": sort if sort in sort_mapping else "newest",
    "meta_labels": meta_labels,
  }
  return render(request, "pages/pruefungen.html", context)
