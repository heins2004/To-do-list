from django.conf import settings
from django.db import models


class Progress(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress",
        null=True,
        blank=True,
    )
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Level {self.level} ({self.xp} XP)"


class Achievement(models.Model):
    KIND_TASKS = "tasks"
    KIND_HABITS = "habits"
    KIND_STREAK = "streak"
    KIND_LEVEL = "level"
    KIND_CHOICES = [
        (KIND_TASKS, "Tasks"),
        (KIND_HABITS, "Habits"),
        (KIND_STREAK, "Streak"),
        (KIND_LEVEL, "Level"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    unlocked = models.BooleanField(default=False)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    threshold = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=8, default="*")
    unlocked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["threshold", "name"]
        unique_together = ("owner", "name")

    def __str__(self) -> str:
        return self.name
