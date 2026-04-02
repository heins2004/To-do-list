import os
from pathlib import Path

try:
    import dj_database_url
except ImportError:  # pragma: no cover
    dj_database_url = None


BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


load_env_file(BASE_DIR / ".env")


def env(key: str, default=None):
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    value = env(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-local-dev-key")
IS_RENDER = bool(env("RENDER")) or bool(env("RENDER_EXTERNAL_HOSTNAME"))
SECRET_KEY = env("DJANGO_SECRET_KEY") or env("SECRET_KEY") or "django-insecure-local-dev-key"
DEBUG = env_bool("DJANGO_DEBUG", not IS_RENDER)

allowed_hosts = {host.strip() for host in env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()}
render_hostname = env("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
    allowed_hosts.add(render_hostname)
if DEBUG:
    allowed_hosts.add("*")
ALLOWED_HOSTS = sorted(allowed_hosts)

csrf_trusted_origins = {
    origin.strip()
    for origin in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
}
if render_hostname:
    csrf_trusted_origins.add(f"https://{render_hostname}")
CSRF_TRUSTED_ORIGINS = sorted(csrf_trusted_origins)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tasks",
    "habits",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    MIDDLEWARE.insert(1, "django.middleware.gzip.GZipMiddleware")
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")


ROOT_URLCONF = "todo_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "todo_site.wsgi.application"


database_url = env("DATABASE_URL")
DB_ENGINE = env("DB_ENGINE", "sqlite").lower()
if database_url and dj_database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
elif DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("MYSQL_DATABASE", "habit_tracker"),
            "USER": env("MYSQL_USER", "root"),
            "PASSWORD": env("MYSQL_PASSWORD", ""),
            "HOST": env("MYSQL_HOST", "127.0.0.1"),
            "PORT": env("MYSQL_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / env("SQLITE_NAME", "db.sqlite3"),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SECURE_BROWSER_XSS_FILTER = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG and IS_RENDER
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
