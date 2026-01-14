from django.contrib import admin
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from apps.exams.models import Category, ContentItem, MetaCategory, MetaOption, SubCategory, UploadBatch, UploadFile
from apps.exams.views import build_zip_response


@admin.action(description="Approve selected")
def approve_selected(modeladmin, request, queryset): queryset.update(status=ContentItem.Status.APPROVED, approved_at=timezone.now())


@admin.action(description="Reject selected")
def reject_selected(modeladmin, request, queryset): queryset.update(status=ContentItem.Status.REJECTED)


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "subject", "teacher", "year", "program", "status", "download_count", "created_at")
    list_filter = ("status", "content_type", "subject", "teacher", "year", "program", "created_at")
    search_fields = ("title", "subject", "teacher")
    actions = (approve_selected, reject_selected)


@admin.action(description="Approve selected batches")
def approve_batches(modeladmin, request, queryset): queryset.update(status=UploadBatch.Status.APPROVED)


@admin.action(description="Reject selected batches")
def reject_batches(modeladmin, request, queryset): queryset.update(status=UploadBatch.Status.REJECTED)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("sort_order", "name")


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "is_active", "sort_order")
    list_filter = ("is_active", "category")
    search_fields = ("name", "slug")
    ordering = ("category", "sort_order", "name")


admin.site.register(MetaCategory)
admin.site.register(MetaOption)


class UploadFileInline(admin.TabularInline):
    model = UploadFile
    extra = 0
    fields = ("original_name", "size", "content_type", "file_link")
    readonly_fields = fields

    @admin.display(description="Datei")
    def file_link(self, obj):
        if not obj.file:
            return "-"
        return format_html('<a href="{}" download>Download</a>', obj.file.url)


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "type_option", "subject_option", "teacher", "year_option", "program_option", "created_at", "file_count", "download_count")
    list_filter = ("status", "type_option", "subject_option", "teacher", "year_option", "program_option", "created_at")
    search_fields = ("teacher__name", "subject_option__label", "files__original_name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = (approve_batches, reject_batches)
    readonly_fields = ("zip_download_link", "review_notice", "created_at", "download_count")
    inlines = (UploadFileInline,)
    list_select_related = ("type_option", "subject_option", "teacher", "year_option", "program_option")
    fieldsets = (
        ("Review", {"fields": ("zip_download_link", "status", "review_notice")}),
        (
            "Metadata",
            {"fields": ("type_option", "subject_option", "teacher", "year_option", "program_option", "created_at", "download_count")},
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:batch_id>/download-zip/",
                self.admin_site.admin_view(self.download_zip),
                name="exams_uploadbatch_zip",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Dateien")
    def file_count(self, obj):
        return obj.files.count()

    @admin.display(description="ZIP herunterladen")
    def zip_download_link(self, obj):
        url = reverse("admin:exams_uploadbatch_zip", args=[obj.pk])
        return format_html('<a class="button" href="{}">ZIP herunterladen</a>', url)

    @admin.display(description="Sicherheitshinweis")
    def review_notice(self, obj):
        return format_html(
            "<strong>Hinweis:</strong> Dateien sind Benutzer-Uploads und sollten vor der Freigabe geprüft werden. "
            "Downloads werden als Anhang bereitgestellt."
        )

    def download_zip(self, request, batch_id):
        batch = get_object_or_404(UploadBatch, pk=batch_id)
        UploadBatch.objects.filter(pk=batch_id).update(download_count=F("download_count") + 1)
        return build_zip_response(
            batch.files.all().order_by("created_at", "id").iterator(),
            f"batch-{batch_id}.zip",
        )

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, True


@admin.register(UploadFile)
class UploadFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "batch", "content_type", "category", "subcategory", "size", "created_at")
    list_filter = ("content_type", "category", "subcategory", "created_at")
    search_fields = ("original_name",)
