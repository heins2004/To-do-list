from django.conf import settings
from django.db import models


class DailyNote(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_notes",
        null=True,
        blank=True,
    )
    date = models.DateField()
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("owner", "date")

    def __str__(self) -> str:
        return f"Note {self.date.isoformat()}"
