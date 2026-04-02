# Habit Tracker + Task Manager

A Django productivity dashboard that combines one-time tasks, daily habits, XP progression, streak tracking, a monthly calendar, and achievement badges in a dark blue RPG-inspired UI.

## Features

- Task manager with deadlines, overdue alerts, and XP rewards
- Habit tracker with daily streak logic and completion logs
- Monthly calendar with completed, pending, and missed status colors
- Dashboard stats, progression bar, and achievement showcase
- AJAX interactions for toggling tasks and habits without page reloads
- `.env`-driven settings with MySQL-ready configuration and `collectstatic` support

## Setup

1. Copy `.env.example` to `.env` and update database credentials.
2. Install your dependencies.
3. Run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.
