from django.contrib import admin
from django.utils import timezone
from apps.exams.models import Category, ContentItem, SubCategory, UploadBatch, UploadFile


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


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "content_type", "category", "subcategory", "status", "created_at")
    list_filter = ("status", "content_type", "category", "subcategory")
    search_fields = ("id", "context")
    actions = (approve_batches, reject_batches)


@admin.register(UploadFile)
class UploadFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "batch", "content_type", "category", "subcategory", "size", "created_at")
    list_filter = ("content_type", "category", "subcategory", "created_at")
    search_fields = ("original_name",)
