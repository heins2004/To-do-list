from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("status", "created_at")

# Register your models here.
