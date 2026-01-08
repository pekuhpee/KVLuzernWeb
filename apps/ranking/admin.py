from django.contrib import admin
from apps.ranking.models import RankingCategory, RankingVote, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(RankingCategory)
class RankingCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order")
    ordering = ("order", "title")
    search_fields = ("title", "slug")


@admin.register(RankingVote)
class RankingVoteAdmin(admin.ModelAdmin):
    list_display = ("category", "teacher", "created_at")
    readonly_fields = ("category", "teacher", "token_hash", "created_at")
    list_select_related = ("category", "teacher")
    ordering = ("-created_at",)
