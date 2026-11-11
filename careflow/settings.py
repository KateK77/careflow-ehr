import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# Local development settings. Use separate settings for any hosted environment.
SECRET_KEY = "django-insecure-careflow-local-development-only"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "careflow.core",
    "careflow.patients",
    "careflow.scheduling",
    "careflow.clinical",
    "careflow.history",
    "careflow.nursing",
    "careflow.labs",
    "careflow.medications",
    "careflow.mar",
    "careflow.portal",
    "careflow.billing",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "careflow.portal.access.PortalBoundary",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "careflow.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "careflow.billing.access.billing_context",
                "django.contrib.messages.context_processors.messages",
                "careflow.patients.access.staff_context",
                "careflow.clinical.access.clinical_context",
                "careflow.nursing.access.nursing_context",
                "careflow.labs.access.lab_context",
                "careflow.medications.access.medication_context",
            ],
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.environ.get("CAREFLOW_DB_PATH", str(BASE_DIR / "db.sqlite3"))),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

STATIC_URL = "static/"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
TIME_ZONE = os.environ.get("CAREFLOW_TIME_ZONE", "America/Chicago")
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
