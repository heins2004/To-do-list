# DoMatrix

DoMatrix is a Django productivity app that combines habit tracking, task planning, daily notes, streaks, reminders, and XP-based progress in a futuristic dashboard UI.

It is designed around two core flows:

- `Habits`: your daily repeatable actions, streaks, skips, and journal notes
- `To-do List`: date-based tasks, reminders, calendar planning, and overdue tracking

## Features

- Daily habit tracker with streaks, skip-today support, and completion history
- To-do list with due dates, reminder windows, and overdue states
- Monthly calendar with date selection and note indicators
- Daily journal/notes saved per date
- XP, levels, and achievement badges
- Dark and light mode with saved preference
- Inline interactions using AJAX without full page reloads

## Screens

### Habit Home

- Opens by default when the app loads
- Shows habits that matter today
- Displays progress, streak, XP, weekly graph, and daily notes
- Supports complete, undo, skip, and undo-skip actions

### To-do Section

- Calendar-driven task planning
- Add and manage tasks by date
- View due-today and overdue work
- Open a selected day to inspect tasks and notes

## Tech Stack

- Python
- Django 4.2
- HTML templates
- CSS
- JavaScript
- SQLite for local development
- PostgreSQL on Render

## Local Development

1. Create and activate a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env`.
4. Run migrations.
5. Start the development server.

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Environment Variables

Common settings used by the project:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_TIME_ZONE`
- `DATABASE_URL`

If `DATABASE_URL` is not provided, the app falls back to SQLite.

## Deployment on Render

This repository is already configured for Render.

### Included Render Files

- `render.yaml`
- `build.sh`
- `requirements.txt`

### What Render Does

- creates a Python web service
- creates a managed PostgreSQL database
- injects `DATABASE_URL`
- installs dependencies
- collects static files
- runs migrations
- starts the app with Gunicorn

### Deploy Steps

1. Push the repository to GitHub.
2. In Render, create a new Blueprint deployment.
3. Connect the repository.
4. Let Render read `render.yaml`.
5. Deploy.

After the build completes, open the generated Render URL.

### Notes

- Review `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` for your production domain if needed.
- If you use the free tier, expect service spin-down and free database limits.

## Project Structure

```text
dashboard/   Dashboard payloads, views, and progress logic
habits/      Habit models, logs, skips, and habit actions
tasks/       Task models, reminders, and task actions
journal/     Daily note storage and endpoints
templates/   Main page and partial templates
static/      CSS and JavaScript assets
todo_site/   Django settings, URLs, and WSGI/ASGI entry points
```

## Key Files

- `dashboard/services.py`  
  Builds the dashboard payload used by the frontend.

- `templates/dashboard/index.html`  
  Main app layout.

- `templates/partials/home_section.html`  
  Habit home screen.

- `templates/partials/tasks_section.html`  
  To-do and calendar section.

- `static/js/app.js`  
  Frontend interactions, AJAX updates, theme toggle, and autosave logic.

- `static/css/app.css`  
  Full app styling, theme variables, and component states.

## Current Capabilities

- Habits can be completed, undone, skipped, and unskipped
- Tasks can be created, completed, reopened, and deleted
- Notes can be written per day and auto-saved
- Calendar dates can show note indicators
- Selected-day detail view can show both scheduled items and notes

## License

This project currently has no license file. Add one if you plan to publish or distribute it publicly.
