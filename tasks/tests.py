from django.test import TestCase
from django.urls import reverse

from .models import Task


class TaskEndpointTests(TestCase):
    def test_create_task_returns_dashboard_payload(self):
        response = self.client.post(
            reverse("task_create"),
            {
                "title": "Ship MVP",
                "description": "Deliver dashboard",
                "due_date": "2026-04-02",
                "type": "main",
                "xp_reward": 50,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.count(), 1)
        self.assertTrue(response.json()["ok"])
