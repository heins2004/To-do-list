from django.test import TestCase
from django.urls import reverse

from .models import Habit, HabitLog, HabitSkip


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

    def test_skip_habit_removes_completion_and_creates_skip(self):
        habit = Habit.objects.create(title="Read", start_date="2026-04-02", xp_reward=25)
        HabitLog.objects.create(habit=habit, completed_on="2026-04-07")

        response = self.client.post(
            reverse("habit_skip", args=[habit.id]),
            data='{"date":"2026-04-07","reason":"Travel"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(HabitLog.objects.filter(habit=habit, completed_on="2026-04-07").exists())
        self.assertTrue(HabitSkip.objects.filter(habit=habit, date="2026-04-07", reason="Travel").exists())
