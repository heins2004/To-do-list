import json
from datetime import date, timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.services import build_dashboard_payload, ensure_achievements, update_achievements

from .forms import HabitForm
from .models import Habit, HabitLog


def calculate_streak(habit: Habit) -> int:
    current_day = habit.last_completed
    if not current_day:
        return 0

    logged_days = set(habit.logs.values_list("completed_on", flat=True))
    streak = 0
    while current_day in logged_days:
        streak += 1
        current_day = current_day - timedelta(days=1)
    return streak


@require_POST
def create_habit(request):
    form = HabitForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    habit = form.save()
    ensure_achievements()
    payload = build_dashboard_payload(selected_date=habit.start_date)
    return JsonResponse({"ok": True, "message": "Habit forged.", "payload": payload})


@require_POST
def toggle_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk)
    body = json.loads(request.body or "{}")
    target_date = date.fromisoformat(body.get("date")) if body.get("date") else timezone.localdate()

    if target_date < habit.start_date:
        return JsonResponse({"ok": False, "message": "Habit has not started yet."}, status=400)

    log = HabitLog.objects.filter(habit=habit, completed_on=target_date).first()
    completed = False
    if log:
        log.delete()
        latest_log = habit.logs.order_by("-completed_on").first()
        habit.last_completed = latest_log.completed_on if latest_log else None
        habit.streak_count = calculate_streak(habit)
        habit.save(update_fields=["last_completed", "streak_count"])
    else:
        HabitLog.objects.create(habit=habit, completed_on=target_date)
        habit.last_completed = max(filter(None, [habit.last_completed, target_date])) if habit.last_completed else target_date
        habit.streak_count = calculate_streak(habit)
        habit.save(update_fields=["last_completed", "streak_count"])
        completed = True

    update_achievements()
    payload = build_dashboard_payload(selected_date=target_date)
    return JsonResponse({"ok": True, "completed": completed, "payload": payload})


@require_POST
def delete_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk)
    habit.delete()
    payload = build_dashboard_payload()
    return JsonResponse({"ok": True, "message": "Habit archive removed.", "payload": payload})
