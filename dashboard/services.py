import calendar
from collections import Counter
from datetime import date, timedelta

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.utils import timezone

from habits.models import Habit, HabitLog
from tasks.models import Task

from .models import Achievement, Progress


XP_PER_LEVEL = 250
ACHIEVEMENT_DEFINITIONS = [
    {"name": "First Blood", "kind": Achievement.KIND_TASKS, "threshold": 1, "description": "Complete your first quest.", "icon": "SB"},
    {"name": "Task Hunter", "kind": Achievement.KIND_TASKS, "threshold": 10, "description": "Clear 10 tasks.", "icon": "TH"},
    {"name": "Daily Disciple", "kind": Achievement.KIND_HABITS, "threshold": 7, "description": "Mark habits complete 7 times.", "icon": "DD"},
    {"name": "Streak Keeper", "kind": Achievement.KIND_STREAK, "threshold": 7, "description": "Reach a 7-day streak.", "icon": "SK"},
    {"name": "Level Breaker", "kind": Achievement.KIND_LEVEL, "threshold": 5, "description": "Climb to level 5.", "icon": "LV"},
]


def ensure_achievements() -> None:
    for definition in ACHIEVEMENT_DEFINITIONS:
        Achievement.objects.get_or_create(name=definition["name"], defaults=definition)


def get_progress() -> Progress:
    ensure_achievements()
    progress, _ = Progress.objects.get_or_create(pk=1)
    return recalculate_progress(progress)


def recalculate_progress(progress: Progress) -> Progress:
    task_xp = sum(task.xp_reward for task in Task.objects.filter(completed=True))
    habits = Habit.objects.prefetch_related("logs")
    habit_xp = sum(habit.logs.count() * habit.xp_reward for habit in habits)
    total_xp = task_xp + habit_xp
    progress.xp = total_xp
    progress.level = max(1, (total_xp // XP_PER_LEVEL) + 1)
    progress.save(update_fields=["xp", "level", "updated_at"])
    update_achievements(progress=progress)
    return progress


def update_achievements(progress: Progress | None = None) -> None:
    ensure_achievements()
    progress = progress or get_progress()
    completed_tasks = Task.objects.filter(completed=True).count()
    habits = Habit.objects.prefetch_related("logs")
    habit_completions = sum(habit.logs.count() for habit in habits)
    top_streak = max((habit.streak_count for habit in habits), default=0)
    now = timezone.now()

    for achievement in Achievement.objects.all():
        metric = {
            Achievement.KIND_TASKS: completed_tasks,
            Achievement.KIND_HABITS: habit_completions,
            Achievement.KIND_STREAK: top_streak,
            Achievement.KIND_LEVEL: progress.level,
        }[achievement.kind]
        should_unlock = metric >= achievement.threshold
        if should_unlock != achievement.unlocked:
            achievement.unlocked = should_unlock
            achievement.unlocked_at = now if should_unlock else None
            achievement.save(update_fields=["unlocked", "unlocked_at"])


def build_dashboard_payload(selected_date: date | None = None) -> dict:
    today = timezone.localdate()
    selected_date = selected_date or today

    habits = list(Habit.objects.prefetch_related(Prefetch("logs", queryset=HabitLog.objects.order_by("-completed_on"))))
    for habit in habits:
        habit.refresh_streak(today=today)

    tasks = list(Task.objects.all())
    progress = get_progress()
    calendar_data = build_calendar(tasks, habits, selected_date)
    selected_items = build_selected_items(selected_date, tasks, habits, today)

    completed_tasks = [task for task in tasks if task.completed]
    pending_tasks = [task for task in tasks if not task.completed]
    overdue_tasks = [task for task in pending_tasks if task.due_date < today]
    completed_habits_today = sum(1 for habit in habits if habit.is_completed_on(today))
    total_habits = len(habits)
    total_possible = len(tasks) + total_habits
    total_completed = len(completed_tasks) + completed_habits_today
    completion_rate = int((total_completed / total_possible) * 100) if total_possible else 0
    next_level_xp = progress.level * XP_PER_LEVEL
    previous_level_xp = (progress.level - 1) * XP_PER_LEVEL
    xp_progress = progress.xp - previous_level_xp
    xp_needed = max(1, next_level_xp - previous_level_xp)
    level_percent = int((xp_progress / xp_needed) * 100)
    top_streak = max((habit.streak_count for habit in habits), default=0)
    achievements = [serialize_achievement(item) for item in Achievement.objects.all()]
    serialized_tasks = [serialize_task(task, today) for task in tasks]
    serialized_habits = [serialize_habit(habit, today, selected_date) for habit in habits]

    payload = {
        "meta": {
            "today": today.isoformat(),
            "selected_date": selected_date.isoformat(),
            "month_label": calendar_data["month_label"],
            "completion_rate": completion_rate,
            "task_completion_rate": int((len(completed_tasks) / len(tasks)) * 100) if tasks else 0,
            "top_streak": top_streak,
            "overdue_count": len(overdue_tasks),
            "habit_completion_rate": int((completed_habits_today / total_habits) * 100) if total_habits else 0,
        },
        "stats": {
            "total_tasks": len(tasks),
            "pending_tasks": len(pending_tasks),
            "completed_tasks": len(completed_tasks),
            "completed_habits_today": completed_habits_today,
            "total_habits": total_habits,
            "overdue_tasks": len(overdue_tasks),
        },
        "progress": {
            "xp": progress.xp,
            "level": progress.level,
            "next_level_xp": next_level_xp,
            "percent": max(0, min(100, level_percent)),
        },
        "tasks": serialized_tasks,
        "habits": serialized_habits,
        "selected_items": selected_items,
        "calendar": calendar_data,
        "achievements": achievements,
        "partials": {},
    }

    payload["partials"] = {
        "task_list": render_to_string("partials/task_list.html", {"tasks": serialized_tasks}),
        "habit_list": render_to_string("partials/habit_list.html", {"habits": serialized_habits, "meta": payload["meta"]}),
        "calendar": render_to_string("partials/calendar.html", {"calendar": calendar_data}),
        "selected_day": render_to_string("partials/selected_day.html", {"selected_items": selected_items, "selected_date": selected_date.isoformat()}),
        "achievements": render_to_string("partials/achievements.html", {"achievements": achievements}),
        "stats": render_to_string("partials/stats.html", {"meta": payload["meta"], "stats": payload["stats"], "progress": payload["progress"]}),
    }
    return payload


def serialize_task(task: Task, today: date) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat(),
        "due_label": task.due_date.strftime("%d %b"),
        "completed": task.completed,
        "type": task.type,
        "type_label": task.get_type_display(),
        "xp_reward": task.xp_reward,
        "state": "completed" if task.completed else ("missed" if task.due_date < today else "pending"),
    }


def serialize_habit(habit: Habit, today: date, selected_date: date) -> dict:
    return {
        "id": habit.id,
        "title": habit.title,
        "description": habit.description,
        "start_date": habit.start_date.isoformat(),
        "streak_count": habit.streak_count,
        "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
        "completed_today": habit.is_completed_on(today),
        "completed_selected_date": habit.is_completed_on(selected_date),
        "xp_reward": habit.xp_reward,
        "selected_state": (
            "future"
            if selected_date < habit.start_date
            else "completed"
            if habit.is_completed_on(selected_date)
            else "missed"
            if selected_date < today
            else "pending"
        ),
    }


def serialize_achievement(item: Achievement) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "icon": item.icon,
        "unlocked": item.unlocked,
    }


def build_selected_items(selected_date: date, tasks: list[Task], habits: list[Habit], today: date) -> list[dict]:
    items = []
    for task in tasks:
        if task.due_date == selected_date:
            items.append(
                {
                    "kind": "task",
                    "title": task.title,
                    "state": task.state,
                    "meta": f"{task.get_type_display()} | {task.xp_reward} XP",
                }
            )
    for habit in habits:
        if selected_date >= habit.start_date:
            items.append(
                {
                    "kind": "habit",
                    "title": habit.title,
                    "state": "completed" if habit.is_completed_on(selected_date) else ("missed" if selected_date < today else "pending"),
                    "meta": f"Streak {habit.streak_count} | {habit.xp_reward} XP",
                }
            )
    return items


def build_calendar(tasks: list[Task], habits: list[Habit], selected_date: date) -> dict:
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(selected_date.year, selected_date.month)
    today = timezone.localdate()

    task_map = Counter()
    completed_task_map = Counter()
    for task in tasks:
        task_map[task.due_date] += 1
        if task.completed:
            completed_task_map[task.due_date] += 1

    habit_logs = Counter()
    for habit in habits:
        for log in habit.logs.all():
            habit_logs[log.completed_on] += 1

    weeks = []
    for week in month_days:
        week_payload = []
        for day in week:
            pending_tasks = task_map[day] - completed_task_map[day]
            habit_count = sum(1 for habit in habits if habit.start_date <= day)
            habit_done = habit_logs[day]

            if completed_task_map[day] or (habit_count and habit_done >= habit_count):
                tone = "green"
            elif day < today and (pending_tasks or (habit_count and habit_done < habit_count)):
                tone = "red"
            elif task_map[day] or habit_count or day >= today:
                tone = "blue"
            else:
                tone = "neutral"

            week_payload.append(
                {
                    "date": day.isoformat(),
                    "day": day.day,
                    "in_month": day.month == selected_date.month,
                    "is_today": day == today,
                    "is_selected": day == selected_date,
                    "tone": tone,
                    "task_count": task_map[day],
                    "habit_count": habit_count,
                }
            )
        weeks.append(week_payload)

    previous_month = (selected_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (selected_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    return {
        "month_label": selected_date.strftime("%B %Y"),
        "selected_date": selected_date.isoformat(),
        "previous_month": previous_month.isoformat(),
        "next_month": next_month.isoformat(),
        "weekdays": list(calendar.day_abbr),
        "weeks": weeks,
    }


def payload_json(payload: dict) -> str:
    return DjangoJSONEncoder().encode(payload)
