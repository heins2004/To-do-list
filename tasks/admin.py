from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "due_date", "completed", "type", "xp_reward")
    list_filter = ("completed", "type", "due_date")
    search_fields = ("title", "description")
