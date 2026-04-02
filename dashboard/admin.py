from django.contrib import admin

from .models import Achievement, Progress


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("xp", "level", "updated_at")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "threshold", "unlocked", "unlocked_at")
    list_filter = ("kind", "unlocked")
