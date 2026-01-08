from django.contrib import admin
from django.utils import timezone

from apps.memes.models import Meme


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at", "approved_at")
    list_filter = ("status", "created_at")
    actions = ("approve_selected", "reject_selected")

    @admin.action(description="Approve selected")
    def approve_selected(self, request, queryset):
        queryset.update(status=Meme.Status.APPROVED, approved_at=timezone.now())

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        queryset.update(status=Meme.Status.REJECTED)
