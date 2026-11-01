"""Database-free API foundation. Environment values are read only on the server."""

import os
import secrets

from django.core.exceptions import ImproperlyConfigured

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
# Ephemeral development secret cannot be used to validate durable signed context.
# A stable configured key is mandatory before signed context/deployment is introduced.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY or explicitly enable local DJANGO_DEBUG.")
    SECRET_KEY = secrets.token_urlsafe(48)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
INSTALLED_APPS = ["rest_framework", "routing"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
DATABASES = {}
USE_TZ = True
TIME_ZONE = "UTC"
APPEND_SLASH = False
DATA_UPLOAD_MAX_MEMORY_SIZE = 256 * 1024
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "weather-routing",
        "OPTIONS": {"MAX_ENTRIES": 2048},
    }
}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "routing.api.errors.exception_handler",
    "DEFAULT_THROTTLE_RATES": {"geocode": "20/minute", "plans": "5/minute", "corridor": "3/minute"},
}
