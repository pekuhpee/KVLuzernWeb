from django.contrib import admin
from django.utils import timezone

from apps.exams.models import ContentItem


@admin.action(description="Approve selected")
def approve_selected(modeladmin, request, queryset):
    queryset.update(status=ContentItem.Status.APPROVED, approved_at=timezone.now())


@admin.action(description="Reject selected")
def reject_selected(modeladmin, request, queryset):
    queryset.update(status=ContentItem.Status.REJECTED)


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "content_type",
        "subject",
        "teacher",
        "year",
        "program",
        "status",
        "download_count",
        "created_at",
    )
    list_filter = (
        "status",
        "content_type",
        "subject",
        "teacher",
        "year",
        "program",
        "created_at",
    )
    search_fields = ("title", "subject", "teacher")
    actions = (approve_selected, reject_selected)
