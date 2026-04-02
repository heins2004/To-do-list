from datetime import timedelta

from django.db import models
from django.utils import timezone


class Habit(models.Model):
    title = models.CharField(max_length=160)
    streak_count = models.PositiveIntegerField(default=0)
    last_completed = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.localdate)
    xp_reward = models.PositiveIntegerField(default=25)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def refresh_streak(self, today=None) -> bool:
        today = today or timezone.localdate()
        if self.last_completed and self.last_completed < today - timedelta(days=1):
            self.streak_count = 0
            self.save(update_fields=["streak_count"])
            return True
        return False

    def is_completed_on(self, date_value) -> bool:
        return self.logs.filter(completed_on=date_value).exists()


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, related_name="logs", on_delete=models.CASCADE)
    completed_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("habit", "completed_on")
        ordering = ["-completed_on"]

    def __str__(self) -> str:
        return f"{self.habit.title} @ {self.completed_on}"
