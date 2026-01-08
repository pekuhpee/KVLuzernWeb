from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from apps.memes.models import Meme


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "preview", "created_at", "approved_at")
    list_filter = ("status", "created_at")
    actions = ("approve_selected", "reject_selected")
    readonly_fields = ("preview",)

    _list_preview_size = 80
    _detail_preview_size = 240

    def get_list_display(self, request):
        self._preview_size = self._list_preview_size
        return super().get_list_display(request)

    def get_readonly_fields(self, request, obj=None):
        self._preview_size = self._detail_preview_size
        return super().get_readonly_fields(request, obj)

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.image:
            return "—"
        size = getattr(self, "_preview_size", self._list_preview_size)
        return format_html(
            '<img src="{}" width="{}" style="height: auto;" />',
            obj.image.url,
            size,
        )

    @admin.action(description="Approve selected")
    def approve_selected(self, request, queryset):
        queryset.update(status=Meme.Status.APPROVED, approved_at=timezone.now())

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        queryset.update(status=Meme.Status.REJECTED)
