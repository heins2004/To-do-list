from django.test import TestCase
from django.urls import reverse

from .models import Habit


class HabitEndpointTests(TestCase):
    def test_create_habit_returns_dashboard_payload(self):
        response = self.client.post(
            reverse("habit_create"),
            {
                "title": "Morning Focus",
                "description": "Deep work session",
                "start_date": "2026-04-02",
                "xp_reward": 25,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Habit.objects.count(), 1)
        self.assertTrue(response.json()["ok"])
