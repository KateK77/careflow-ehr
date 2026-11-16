import importlib
import os
import secrets
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from .models import Enrollment


class HostedSettingsTests(SimpleTestCase):
    def settings(self, **changes):
        values = {
            "CAREFLOW_HOSTED_DEMO": "1", "CAREFLOW_SECRET_KEY": secrets.token_urlsafe(48),
            "CAREFLOW_PUBLIC_ORIGIN": "https://demo.example.invalid",
            "CAREFLOW_HOSTED_DB": str(Path(tempfile.gettempdir()) / "hosted-demo-unused.sqlite3"),
            
        }
        values.update(changes)
        with patch.dict(os.environ, values):
            sys.modules.pop("careflow.settings_hosted_demo", None)
            return importlib.import_module("careflow.settings_hosted_demo")

    def tearDown(self):
        sys.modules.pop("careflow.settings_hosted_demo", None)

    def test_hosted_settings_require_https_secure_cookies_and_no_mail_service(self):
        module = self.settings()
        self.assertFalse(module.DEBUG)
        self.assertEqual(module.ALLOWED_HOSTS, ["demo.example.invalid"])
        self.assertTrue(module.SECURE_SSL_REDIRECT and module.CSRF_COOKIE_SECURE and module.SESSION_COOKIE_SECURE)
        self.assertEqual(module.EMAIL_BACKEND, "django.core.mail.backends.dummy.EmailBackend")
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", module.MIDDLEWARE)

    def test_hosted_settings_reject_missing_secrets_and_insecure_origin(self):
        for changes in (
            {"CAREFLOW_SECRET_KEY": ""}, {"CAREFLOW_SECRET_KEY": "short"},
            {"CAREFLOW_PUBLIC_ORIGIN": "http://demo.example.invalid"},
            {"CAREFLOW_PUBLIC_ORIGIN": "https://localhost"}, {"CAREFLOW_PUBLIC_ORIGIN": "https://demo.example.invalid/path"},
            {"CAREFLOW_HOSTED_DEMO": "0"}, {"CAREFLOW_HOSTED_DB": "db.sqlite3"},
        ):
            with self.subTest(fields=list(changes)), self.assertRaises(ImproperlyConfigured):
                self.settings(**changes)

    def test_hosted_database_cannot_be_the_repository_database(self):
        from django.conf import settings
        with self.assertRaises(ImproperlyConfigured):
            self.settings(CAREFLOW_HOSTED_DB=str(settings.BASE_DIR / "db.sqlite3"))


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OperatorBootstrapTests(TestCase):
    def test_bootstrap_creates_only_first_admin_without_superuser_and_never_resets(self):
        password = secrets.token_urlsafe(24)
        with patch("careflow.accounts.management.commands.bootstrap_demo_operator.getpass.getpass",
                   side_effect=[password, password]):
            call_command("bootstrap_demo_operator", username="operator", confirm_synthetic=True, stdout=StringIO())
        user = get_user_model().objects.get()
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_superuser or user.is_staff)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Administrator"])
        self.assertEqual(Enrollment.objects.get().events.get().action, "operator_bootstrap")
        with self.assertRaises(CommandError):
            call_command("bootstrap_demo_operator", username="another", confirm_synthetic=True, stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_bootstrap_requires_explicit_synthetic_confirmation(self):
        with self.assertRaises(CommandError):
            call_command("bootstrap_demo_operator", username="operator", stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 0)
