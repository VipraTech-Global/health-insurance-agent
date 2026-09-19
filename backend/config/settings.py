import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-only-change-me-" + "x" * 32)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
COVERGUIDE_V2_ENABLED = os.environ.get("COVERGUIDE_V2_ENABLED", "1") == "1"
ALLOWED_HOSTS = [
    item
    for item in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if item
]
CSRF_TRUSTED_ORIGINS = [
    item
    for item in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:8088,http://127.0.0.1:8088",
    ).split(",")
    if item
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "apps.accounts",
    "apps.adviser",
]
if COVERGUIDE_V2_ENABLED:
    INSTALLED_APPS.append("apps.adviser_v2")
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "health_adviser"),
        "USER": os.environ.get("POSTGRES_USER", "health_adviser"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "health_adviser_local"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "55449"),
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"pool": {"min_size": 1, "max_size": 8, "timeout": 5}},
    }
}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR.parent / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SECURE_COOKIES", "0") == "1"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
DATA_ROOT = Path(os.environ.get("DATA_ROOT", BASE_DIR.parent / "data"))
USE_X_ACCEL_REDIRECT = os.environ.get("USE_X_ACCEL_REDIRECT", "1") == "1"
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6398/8")
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BEAT_SCHEDULE = {
    "reconcile-abandoned-turns": {
        "task": "apps.adviser.tasks.reconcile_abandoned_turns",
        "schedule": 30.0,
    }
}
if COVERGUIDE_V2_ENABLED:
    CELERY_BEAT_SCHEDULE.update(
        {
            "dispatch-v2-outbox": {
                "task": "adviser_v2.dispatch_outbox",
                "schedule": 5.0,
                "options": {"queue": "conversation"},
            },
            "recover-v2-expired-work": {
                "task": "adviser_v2.recover_expired_work",
                "schedule": 30.0,
                "options": {"queue": "conversation"},
            },
        }
    )
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6398/8")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"pool_class": "redis.BlockingConnectionPool"},
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.adviser.errors.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Health Insurance Adviser API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "apps.adviser.schema.add_native_view_contracts",
    ],
}

# Server-only configuration. Both applications deliberately share account-operation locks.
AI_RELAY_BASE_URL = os.environ.get("AI_RELAY_BASE_URL", "http://127.0.0.1:8317")
AI_RELAY_API_KEY = os.environ.get("AI_RELAY_API_KEY", "")
AI_RELAY_MANAGEMENT_KEY = os.environ.get("AI_RELAY_MANAGEMENT_KEY", "")
AI_RELAY_STATE_DIR = Path(
    os.environ.get("AI_RELAY_STATE_DIR", "~/.local/state/job-in/relay-accounts")
).expanduser()
AI_TURN_TIMEOUT_SECONDS = int(os.environ.get("AI_TURN_TIMEOUT_SECONDS", "240"))

# CoverGuide v2 server-only privacy and frozen-corpus settings. Key-ring entries use
# ``key-id:base64url-encoded-32-byte-key`` and are ordered newest first. DEBUG derives
# an isolated local key from SECRET_KEY only when no ring is supplied.
COVERGUIDE_ENCRYPTION_KEYS = os.environ.get("COVERGUIDE_ENCRYPTION_KEYS", "")
COVERGUIDE_COMMITMENT_KEYS = os.environ.get("COVERGUIDE_COMMITMENT_KEYS", "")
COVERGUIDE_V2_STORAGE_ROOT = Path(os.environ.get("COVERGUIDE_V2_STORAGE_ROOT", DATA_ROOT / "v2"))
COVERGUIDE_MANIFEST_ROOT = Path(
    os.environ.get("COVERGUIDE_MANIFEST_ROOT", BASE_DIR.parent / "data" / "manifests")
)
COVERGUIDE_REPORT_ROOT = Path(
    os.environ.get("COVERGUIDE_REPORT_ROOT", BASE_DIR.parent / "data" / "reports")
)
COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL = "gpt-5.6-luna"
COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol"
COVERGUIDE_POLICY_REVIEW_MODEL = "gpt-5.6-terra"
COVERGUIDE_FINAL_EXPLANATION_MODEL = "gpt-5.6-sol"
COVERGUIDE_EMBEDDING_DIMENSIONS = 1024
COVERGUIDE_EMBEDDING_MODEL_PATH = os.environ.get("COVERGUIDE_EMBEDDING_MODEL_PATH", "")
COVERGUIDE_EMBEDDING_QUALIFICATION_PATH = os.environ.get(
    "COVERGUIDE_EMBEDDING_QUALIFICATION_PATH", ""
)
COVERGUIDE_DOCLING_ARTIFACTS_PATH = os.environ.get("COVERGUIDE_DOCLING_ARTIFACTS_PATH", "")
COVERGUIDE_TESSERACT_PATH = os.environ.get("COVERGUIDE_TESSERACT_PATH", "")
