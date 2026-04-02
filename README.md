# DoMatrix

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

## Deploy on Render

Render's current Django deployment guide uses a managed PostgreSQL database, `DATABASE_URL`, WhiteNoise for static files, and a build/start flow defined in your repo.

Files added for deployment:

- `requirements.txt`
- `build.sh`
- `render.yaml`

Recommended steps:

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and connect the GitHub repo.
3. Render will read `render.yaml`, create:
   - one web service
   - one PostgreSQL database
4. Deploy the service and open the generated Render URL.

Important notes:

- The Render deployment path uses PostgreSQL, not MySQL.
- Local development can still use SQLite or MySQL via `.env`.
- Set any custom domain in `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

Official docs used:

- https://render.com/docs/deploy-django
- https://render.com/docs/blueprint-spec
