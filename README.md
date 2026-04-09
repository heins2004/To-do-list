# DoMatrix

DoMatrix is a multi-app Django productivity system that combines task scheduling, habit tracking, daily notes, streak management, and XP-based progression behind a single authenticated dashboard.

The project is implemented as a server-rendered Django application with HTML templates, static JavaScript, and JSON endpoints used to refresh sections of the UI without a full page reload.

## System Overview

The application is organized around four main domains:

- `tasks`: dated work items with completion state, quest type, reminder lead time, and XP reward
- `habits`: repeatable actions with completion logs, skip records, start dates, and streak calculation
- `journal`: one note per user per day
- `dashboard`: aggregation layer that builds the full dashboard payload consumed by the frontend

Authentication and account management are handled in the `accounts` app using Django's built-in auth system.

## Architecture

### Request / Response Model

- The main dashboard route renders `templates/dashboard/index.html`
- `dashboard.services.build_dashboard_payload()` assembles the current application state for the logged-in user
- The initial payload is injected into the template and also serialized as JSON for client-side hydration
- Mutating actions such as creating tasks, toggling habits, or saving notes return JSON responses containing an updated dashboard payload
- Frontend JavaScript replaces the relevant partials instead of forcing a full navigation

This keeps the project closer to classic Django than a standalone SPA while still supporting a responsive UI.

### Data Flow

1. A user submits an action from the dashboard.
2. The relevant app view validates the request and updates the database.
3. The view calls `build_dashboard_payload()` for the current user.
4. The response returns normalized data plus rendered HTML partials.
5. The browser swaps the affected UI sections in place.

## Domain Model

### Tasks

Defined in `tasks/models.py`.

- `Task` stores `title`, `description`, `due_date`, `reminder_days_before`, `completed`, `type`, and `xp_reward`
- Task type is modeled with fixed choices: `main`, `side`, and `boss`
- `Task.state` derives a UI-facing state: `completed`, `missed`, or `pending`
- Tasks are ordered by completion status, due date, and creation time

### Habits

Defined in `habits/models.py`.

- `Habit` stores ownership, descriptive fields, `start_date`, `xp_reward`, `last_completed`, and `streak_count`
- `HabitLog` records one completion per habit per date
- `HabitSkip` records one skip per habit per date with an optional reason
- Unique constraints prevent duplicate logs or duplicate skips for the same day
- Streak state is recalculated from completion history in `habits/views.py`

### Notes

Defined in `journal/models.py`.

- `DailyNote` stores one note per user per date
- Empty note submissions delete the record instead of storing blank content

### Progress and Achievements

Aggregated in `dashboard/services.py`.

- XP is computed from completed tasks and habit logs
- Level progression uses a fixed threshold of `250 XP` per level
- Achievements are materialized per user and unlocked when thresholds are reached

## Dashboard Aggregation

`dashboard/services.py` is the core orchestration layer. It is responsible for:

- recalculating XP and level state
- ensuring achievement records exist
- computing overdue tasks, due-today tasks, reminders, and pending habits
- generating the month calendar payload
- generating a 7-day habit graph
- serializing tasks, habits, notes, achievements, and selected-day items
- rendering HTML partials for the home view, tasks view, alerts sheet, and day sheet

This means most UI screens depend on a single consolidated payload rather than many independent template contexts.

## Technology Stack

- Python 3
- Django 4.2
- SQLite for default local development
- PostgreSQL when `DATABASE_URL` is provided in deployment
- WhiteNoise for static asset serving in non-debug environments
- Gunicorn as the production WSGI server
- HTML templates, CSS, and vanilla JavaScript for the frontend

## Configuration

Environment loading is implemented directly in `todo_site/settings.py`; the project does not require `python-dotenv`.

### Supported Environment Variables

- `DJANGO_SECRET_KEY`: Django secret key
- `SECRET_KEY`: fallback alias for the secret key
- `DJANGO_DEBUG`: enables debug mode when set to a truthy value
- `DJANGO_ALLOWED_HOSTS`: comma-separated allowed hosts
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated trusted origins
- `DJANGO_TIME_ZONE`: application timezone, defaults to `Asia/Kolkata`
- `DATABASE_URL`: enables `dj-database-url` parsing, intended for PostgreSQL on Render
- `DB_ENGINE`: set to `mysql` to use the MySQL branch in settings
- `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`: MySQL settings
- `SQLITE_NAME`: alternate SQLite file name for local development

### Database Selection Logic

- If `DATABASE_URL` exists, it is used as the primary database configuration
- Else if `DB_ENGINE=mysql`, Django uses the MySQL configuration block
- Otherwise the application falls back to SQLite at `BASE_DIR / db.sqlite3`

## Local Development

### Prerequisites

- Python 3.10+ recommended
- `pip`
- virtual environment tooling

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

### Optional Validation

```bash
python manage.py check
python manage.py test
```

## Deployment

The repository includes Render-specific deployment files:

- `render.yaml`
- `build.sh`
- `requirements.txt`

On Render, the expected flow is:

1. Render creates the web service from `render.yaml`
2. Dependencies are installed from `requirements.txt`
3. Static files are collected
4. Database migrations are applied
5. Gunicorn starts the Django application

In non-debug mode the project enables:

- `GZipMiddleware`
- `WhiteNoiseMiddleware`
- secure cookie settings
- SSL redirect behavior when running on Render

## Project Layout

```text
accounts/      Authentication and account views/forms
dashboard/     Dashboard payload generation, progress, achievements, views
habits/        Habit models, forms, endpoints, streak/skip logic
journal/       Daily note storage and note endpoints
tasks/         Task models, forms, and task mutation endpoints
templates/     Base template, dashboard template, and partial fragments
static/        Frontend CSS and JavaScript assets
todo_site/     Project settings, root URLs, WSGI, and ASGI entry points
manage.py      Django management entry point
```

## Key Files

- `todo_site/settings.py`: environment loading, middleware, database selection, static storage, and security flags
- `dashboard/services.py`: central payload builder and dashboard aggregation logic
- `dashboard/views.py`: dashboard page render and snapshot endpoint
- `tasks/views.py`: create, toggle, and delete task endpoints
- `habits/views.py`: create, toggle, skip, undo-skip, and delete habit endpoints
- `journal/views.py`: save and fetch daily note endpoints
- `templates/dashboard/index.html`: root dashboard template
- `static/js/app.js`: client-side interactions and partial refresh handling

## Behavior Summary

- Each user owns their own tasks, habits, notes, progress, and achievements
- Habit completion and skip actions are date-aware rather than only "today"-aware
- Overdue task state is derived dynamically from `due_date` and `completed`
- Notes are stored per calendar date and surfaced in both the calendar and selected-day views
- The dashboard computes both raw counts and presentation-oriented metadata for the UI

## License

No license file is currently present in the repository. Add one before distributing the project publicly.
