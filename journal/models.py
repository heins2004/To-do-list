from django.db import models


class DailyNote(models.Model):
    date = models.DateField(unique=True)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"Note {self.date.isoformat()}"
