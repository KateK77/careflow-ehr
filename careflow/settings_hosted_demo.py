"""Fail-closed settings for a small, explicitly provisioned synthetic public demo."""
import os
from pathlib import Path
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured
from .settings import *  # noqa: F403


def required(name):
    value = os.environ.get(name, "")
    if not value:
        raise ImproperlyConfigured(f"Required hosted setting is missing: {name}")
    return value


if required("CAREFLOW_HOSTED_DEMO") != "1":
    raise ImproperlyConfigured("Explicit hosted synthetic-demo enablement is required.")
SECRET_KEY = required("CAREFLOW_SECRET_KEY")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured("Use a strong, independently generated hosted secret.")
DEBUG = False
CAREFLOW_PUBLIC_ORIGIN = required("CAREFLOW_PUBLIC_ORIGIN").rstrip("/")
origin = urlsplit(CAREFLOW_PUBLIC_ORIGIN)
if (origin.scheme != "https" or not origin.hostname or origin.username or origin.password
        or origin.path or origin.query or origin.fragment or "*" in origin.hostname
        or origin.hostname in ("localhost", "127.0.0.1", "::1")):
    raise ImproperlyConfigured("Use one public HTTPS origin without a path or credentials.")
ALLOWED_HOSTS = [origin.hostname]
CSRF_TRUSTED_ORIGINS = [CAREFLOW_PUBLIC_ORIGIN]
database = Path(required("CAREFLOW_HOSTED_DB")).expanduser()
if not database.is_absolute() or database.resolve().is_relative_to(BASE_DIR.resolve()):
    raise ImproperlyConfigured("Hosted SQLite must be on persistent storage outside the source directory.")
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": database,
                          "OPTIONS": {"timeout": 20}}}
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Enable only behind a trusted proxy that removes spoofed forwarding headers.
if os.environ.get("CAREFLOW_TRUST_HTTPS_PROXY") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
# Account registration uses usernames, not mail services.
