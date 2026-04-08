from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    TYPE_MAIN = "main"
    TYPE_SIDE = "side"
    TYPE_BOSS = "boss"
    TYPE_CHOICES = [
        (TYPE_MAIN, "Main Quest"),
        (TYPE_SIDE, "Side Quest"),
        (TYPE_BOSS, "Boss Fight"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    due_date = models.DateField(default=timezone.localdate)
    reminder_days_before = models.PositiveIntegerField(default=1)
    completed = models.BooleanField(default=False)
    type = models.CharField(max_length=12, choices=TYPE_CHOICES, default=TYPE_MAIN)
    xp_reward = models.PositiveIntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["completed", "due_date", "-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_overdue(self) -> bool:
        return not self.completed and self.due_date < timezone.localdate()

    @property
    def state(self) -> str:
        if self.completed:
            return "completed"
        if self.is_overdue:
            return "missed"
        return "pending"
