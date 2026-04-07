import calendar
from collections import Counter
from datetime import date, timedelta

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.utils import timezone

from habits.models import Habit, HabitLog, HabitSkip
from journal.models import DailyNote
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

    habits = list(
        Habit.objects.prefetch_related(
            Prefetch("logs", queryset=HabitLog.objects.order_by("-completed_on")),
            Prefetch("skips", queryset=HabitSkip.objects.order_by("-date")),
        )
    )
    for habit in habits:
        habit.refresh_streak(today=today)

    tasks = list(Task.objects.all())
    notes = list(DailyNote.objects.all())
    note_map = {note.date: note for note in notes}
    progress = get_progress()
    calendar_data = build_calendar(tasks, habits, selected_date, note_map)
    selected_items = build_selected_items(selected_date, tasks, habits, today)
    weekly_habit_graph = build_weekly_habit_graph(habits, today)
    today_note = serialize_note(note_map.get(today))
    selected_note = serialize_note(note_map.get(selected_date))

    completed_tasks = [task for task in tasks if task.completed]
    pending_tasks = [task for task in tasks if not task.completed]
    overdue_tasks = [task for task in pending_tasks if task.due_date < today]
    today_tasks = [task for task in pending_tasks if task.due_date == today]
    upcoming_reminders = [
        task for task in pending_tasks if today < task.due_date <= today + timedelta(days=task.reminder_days_before)
    ]
    due_habits = [
        habit
        for habit in habits
        if habit.start_date <= today and not habit.is_completed_on(today) and not habit.is_skipped_on(today)
    ]
    completed_habits_today = sum(1 for habit in habits if habit.is_completed_on(today))
    skipped_habits_today = sum(1 for habit in habits if habit.is_skipped_on(today))
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
    home_habits = [habit for habit in serialized_habits if habit["start_date"] <= today.isoformat()]
    due_habit_cards = [habit for habit in home_habits if not habit["completed_today"] and not habit["skipped_today"]]
    home_habits.sort(
        key=lambda item: (
            item["completed_today"],
            item["skipped_today"],
            -item["streak_count"],
            item["title"].lower(),
        )
    )

    alerts = build_alerts(
        today=today,
        due_habits=due_habit_cards,
        today_tasks=serialized_task_subset(today_tasks, today),
        upcoming=serialized_task_subset(upcoming_reminders, today),
        overdue=serialized_task_subset(overdue_tasks, today),
    )

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
            "tasks_due_today": len(today_tasks),
            "reminder_count": len(upcoming_reminders),
            "pending_habits_today": len(due_habits),
            "skipped_habits_today": skipped_habits_today,
            "task_nav_badge": len(overdue_tasks) or len(today_tasks),
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
        "home_habits": home_habits,
        "selected_items": selected_items,
        "calendar": calendar_data,
        "alerts": alerts,
        "weekly_habit_graph": weekly_habit_graph,
        "today_note": today_note,
        "selected_note": selected_note,
        "calendar_years": list(range(today.year - 3, today.year + 5)),
        "achievements": achievements,
        "partials": {},
    }

    payload["partials"] = {
        "home_section": render_to_string(
            "partials/home_section.html",
            {
                "habits": home_habits,
                "meta": payload["meta"],
                "stats": payload["stats"],
                "progress": payload["progress"],
                "alerts": alerts,
                "weekly_habit_graph": weekly_habit_graph,
                "today_note": today_note,
                "achievements": achievements,
            },
        ),
        "tasks_section": render_to_string(
            "partials/tasks_section.html",
            {
                "tasks": serialized_tasks,
                "calendar": calendar_data,
                "selected_items": selected_items,
                "selected_date": selected_date.isoformat(),
                "meta": payload["meta"],
                "calendar_years": payload["calendar_years"],
                "selected_note": selected_note,
            },
        ),
        "alert_sheet": render_to_string("partials/alert_sheet.html", {"alerts": alerts, "meta": payload["meta"]}),
        "day_sheet": render_to_string(
            "partials/day_sheet.html",
            {
                "selected_items": selected_items,
                "selected_date": selected_date.isoformat(),
                "selected_note": selected_note,
                "meta": payload["meta"],
            },
        ),
    }
    return payload


def serialized_task_subset(tasks: list[Task], today: date) -> list[dict]:
    return [serialize_task(task, today) for task in tasks]


def build_alerts(today: date, due_habits: list[dict], today_tasks: list[dict], upcoming: list[dict], overdue: list[dict]) -> dict:
    summary = []
    if due_habits:
        summary.append(f"{len(due_habits)} habits left today")
    if today_tasks:
        summary.append(f"{len(today_tasks)} tasks due today")
    if overdue:
        summary.append(f"{len(overdue)} overdue")
    if upcoming:
        summary.append(f"{len(upcoming)} upcoming reminders")

    return {
        "headline": "Nothing urgent right now." if not summary else "Today needs attention.",
        "summary": " | ".join(summary) if summary else "You are clear for now.",
        "due_habits": due_habits,
        "today_tasks": today_tasks,
        "upcoming_tasks": upcoming,
        "overdue_tasks": overdue,
        "has_items": bool(summary),
        "today": today.isoformat(),
    }


def serialize_task(task: Task, today: date) -> dict:
    days_until_due = (task.due_date - today).days
    reminder_start = task.due_date - timedelta(days=task.reminder_days_before)
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
        "reminder_days_before": task.reminder_days_before,
        "days_until_due": days_until_due,
        "reminder_active": today >= reminder_start and not task.completed,
        "state": "completed" if task.completed else ("missed" if task.due_date < today else "pending"),
    }


def serialize_habit(habit: Habit, today: date, selected_date: date) -> dict:
    completed_today = habit.is_completed_on(today)
    skipped_today = habit.is_skipped_on(today)
    selected_skip = habit.skips.filter(date=selected_date).first()
    today_skip = habit.skips.filter(date=today).first()
    return {
        "id": habit.id,
        "title": habit.title,
        "description": habit.description,
        "start_date": habit.start_date.isoformat(),
        "streak_count": habit.streak_count,
        "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
        "completed_today": completed_today,
        "skipped_today": skipped_today,
        "skip_reason_today": today_skip.reason if today_skip else "",
        "completed_selected_date": habit.is_completed_on(selected_date),
        "skipped_selected_date": bool(selected_skip),
        "skip_reason_selected_date": selected_skip.reason if selected_skip else "",
        "xp_reward": habit.xp_reward,
        "progress_percent": 100 if completed_today or skipped_today else 0,
        "selected_state": (
            "future"
            if selected_date < habit.start_date
            else "completed"
            if habit.is_completed_on(selected_date)
            else "skipped"
            if selected_skip
            else "missed"
            if selected_date < today
            else "pending"
        ),
    }


def build_weekly_habit_graph(habits: list[Habit], today: date) -> list[dict]:
    week_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    total_habits = len([habit for habit in habits if habit.start_date <= today])
    graph = []

    for day in week_days:
        active_habits = [habit for habit in habits if habit.start_date <= day]
        completed_count = sum(1 for habit in active_habits if habit.is_completed_on(day))
        skipped_count = sum(1 for habit in active_habits if habit.is_skipped_on(day))
        denominator = len(active_habits) or total_habits or 1
        percent = int(((completed_count + skipped_count) / denominator) * 100) if active_habits else 0
        tone = "completed" if completed_count else "skipped" if skipped_count else "missed"
        graph.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "completed": completed_count,
                "skipped": skipped_count,
                "total": len(active_habits),
                "percent": percent,
                "tone": tone,
            }
        )

    return graph


def serialize_achievement(item: Achievement) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "icon": item.icon,
        "unlocked": item.unlocked,
    }


def serialize_note(note: DailyNote | None) -> dict:
    return {
        "date": note.date.isoformat() if note else None,
        "content": note.content if note else "",
        "has_note": bool(note and note.content.strip()),
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
                    "meta": f"{task.get_type_display()} | {task.xp_reward} XP | Remind {task.reminder_days_before} day(s) early",
                }
            )
    for habit in habits:
        if selected_date >= habit.start_date:
            skip = habit.skips.filter(date=selected_date).first()
            items.append(
                {
                    "kind": "habit",
                    "title": habit.title,
                    "state": "completed"
                    if habit.is_completed_on(selected_date)
                    else "skipped"
                    if skip
                    else ("missed" if selected_date < today else "pending"),
                    "meta": f"Streak {habit.streak_count} | {habit.xp_reward} XP"
                    + (f" | Skipped: {skip.reason}" if skip and skip.reason else " | Skipped" if skip else ""),
                }
            )
    return items


def build_calendar(tasks: list[Task], habits: list[Habit], selected_date: date, note_map: dict[date, DailyNote]) -> dict:
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
            item_count = task_map[day] + habit_count

            if completed_task_map[day] or (habit_count and habit_done >= habit_count):
                tone = "green"
            elif day < today and (pending_tasks or (habit_count and habit_done < habit_count)):
                tone = "red"
            elif item_count or day >= today:
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
                    "item_count": item_count,
                    "has_note": bool(note_map.get(day) and note_map[day].content.strip()),
                }
            )
        weeks.append(week_payload)

    previous_month = (selected_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (selected_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    return {
        "month_label": selected_date.strftime("%B %Y"),
        "selected_date": selected_date.isoformat(),
        "selected_month": selected_date.strftime("%m"),
        "selected_year": str(selected_date.year),
        "previous_month": previous_month.isoformat(),
        "next_month": next_month.isoformat(),
        "weekdays": list(calendar.day_abbr),
        "weeks": weeks,
    }


def payload_json(payload: dict) -> str:
    return DjangoJSONEncoder().encode(payload)
