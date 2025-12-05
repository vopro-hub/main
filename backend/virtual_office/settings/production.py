# virtual_office/settings/production.py
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
ENV = os.getenv

DEBUG = False
SECRET_KEY = ENV("SECRET_KEY")

ALLOWED_HOSTS = ["*"]

BACKEND_URL = ENV("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = ENV("FRONTEND_URL", "http://localhost:3000")
DOMAIN = ENV("DOMAIN", "http://localhost")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": ENV("DATABASE_NAME", ENV("POSTGRES_DB")),
        "USER": ENV("DATABASE_USER", ENV("POSTGRES_USER")),
        "PASSWORD": ENV("DATABASE_PASSWORD", ENV("POSTGRES_PASSWORD")),
        "HOST": ENV("DATABASE_HOST", "db"),
        "PORT": ENV("DATABASE_PORT", "5432"),
    }
}

REDIS_URL = ENV("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = ENV("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = ENV("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [ENV("CHANNEL_LAYERS_BACKEND", "redis://redis:6379/3")],
        },
    },
}

ASGI_APPLICATION = "virtual_office.asgi.application"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=int(ENV("SIMPLE_JWT_ACCESS_TOKEN_LIFETIME", 300))),
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=int(ENV("SIMPLE_JWT_REFRESH_TOKEN_LIFETIME", 604800))),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [FRONTEND_URL]

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = ENV("STATIC_ROOT", "/vol/web/static")
MEDIA_ROOT = ENV("MEDIA_ROOT", "/vol/web/media")

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
