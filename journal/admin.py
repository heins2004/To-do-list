from django.contrib import admin

from .models import DailyNote


@admin.register(DailyNote)
class DailyNoteAdmin(admin.ModelAdmin):
    list_display = ("date", "updated_at")
    search_fields = ("date", "content")
