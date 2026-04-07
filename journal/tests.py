from django.test import TestCase
from django.urls import reverse

from .models import DailyNote


class JournalEndpointTests(TestCase):
    def test_save_note_creates_and_get_returns_content(self):
        response = self.client.post(
            reverse("journal_save"),
            data='{"date":"2026-04-07","content":"Reflect on the day"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(DailyNote.objects.filter(date="2026-04-07").exists())

        get_response = self.client.get(reverse("journal_get", args=["2026-04-07"]))
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["content"], "Reflect on the day")
