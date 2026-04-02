from django.contrib import admin

from .models import Habit, HabitLog


class HabitLogInline(admin.TabularInline):
    model = HabitLog
    extra = 0


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("title", "streak_count", "last_completed", "xp_reward")
    search_fields = ("title", "description")
    inlines = [HabitLogInline]


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ("habit", "completed_on", "created_at")
    list_filter = ("completed_on",)
