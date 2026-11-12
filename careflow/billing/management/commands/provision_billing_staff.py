import getpass
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from careflow.patients.models import AuditEvent


class Command(BaseCommand):
    help = "Create a new synthetic BillingStaff account in a Phase 6 preview."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--confirm-preview", required=True, action="store_true")

    def handle(self, *args, **options):
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if (not os.environ.get("CAREFLOW_DB_PATH") or not target.is_file()
                or target.parent != (settings.BASE_DIR / ".venv").resolve()
                or target.name not in {"phase6-a-preview.sqlite3", "phase6-b-preview.sqlite3"}):
            raise CommandError("Select an explicit Phase 6 preview database.")
        user = get_user_model()(username=options["username"])
        if get_user_model().objects.filter(username=user.username).exists():
            raise CommandError("This username already exists.")
        if not os.isatty(0):
            raise CommandError("Run in an interactive terminal for hidden password entry.")
        password = getpass.getpass("New synthetic BillingStaff password: ")
        try:
            user.full_clean(exclude=["password"])
            validate_password(password, user)
            with transaction.atomic():
                user.set_password(password)
                user.save(force_insert=True)
                role, _ = Group.objects.get_or_create(name="BillingStaff")
                user.groups.add(role)
                AuditEvent.objects.create(action="billing_staff_provision")
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from None
        except IntegrityError:
            raise CommandError("The username already exists.") from None
        self.stdout.write(self.style.SUCCESS(f"Created {user.username} with BillingStaff permissions."))
