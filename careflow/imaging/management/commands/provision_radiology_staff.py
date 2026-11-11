import getpass
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, connection, transaction

from careflow.imaging.models import ExamWorkflow
from careflow.patients.models import AuditEvent


class Command(BaseCommand):
    help = "Create a new synthetic RadiologyStaff login in the Phase 7B preview."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--confirm-preview", action="store_true", required=True)

    def handle(self, *args, **options):
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        preview = (settings.BASE_DIR / ".venv" / "phase7-b-preview.sqlite3").resolve()
        if not os.environ.get("CAREFLOW_DB_PATH") or target != preview or not target.is_file():
            raise CommandError("Select the existing Phase 7B preview database.")
        if ExamWorkflow._meta.db_table not in connection.introspection.table_names():
            raise CommandError("The selected preview does not have the Radiology Workspace schema.")
        user_model = get_user_model()
        user = user_model(username=options["username"])
        if user_model.objects.filter(username=user.username).exists():
            raise CommandError("This username already exists.")
        if not os.isatty(0):
            raise CommandError("Use an interactive terminal for the hidden password prompt.")
        password = getpass.getpass("New synthetic RadiologyStaff password: ")
        try:
            user.full_clean(exclude=["password"])
            validate_password(password, user)
            with transaction.atomic():
                user.set_password(password)
                user.save(force_insert=True)
                role, _ = Group.objects.get_or_create(name="RadiologyStaff")
                user.groups.add(role)
                AuditEvent.objects.create(action="radiology_staff_provision")
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from None
        except IntegrityError:
            raise CommandError("This username already exists.") from None
        self.stdout.write(self.style.SUCCESS(f"Created {user.username} with RadiologyStaff permissions."))
