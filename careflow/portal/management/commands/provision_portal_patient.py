import getpass
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, connection, transaction

from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientPortalAccount


class Command(BaseCommand):
    help = "Create a new linked synthetic login in a migrated Phase 5 preview."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--patient-id", type=int, required=True)
        parser.add_argument("--confirm-preview", action="store_true", required=True)

    def handle(self, *args, **options):
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if (not os.environ.get("CAREFLOW_DB_PATH") or not target.is_file()
                or target.parent != (settings.BASE_DIR / ".venv").resolve()
                or target.name not in {"phase5-a-preview.sqlite3", "phase5-b-preview.sqlite3",
                                    "phase6-a-preview.sqlite3", "phase6-b-preview.sqlite3"}):
            raise CommandError("Select an explicit Phase 5 or Phase 6 preview database.")
        if PatientPortalAccount._meta.db_table not in connection.introspection.table_names():
            raise CommandError("The selected preview does not have the portal schema.")
        patient = Patient.objects.filter(pk=options["patient_id"]).first()
        if patient is None:
            raise CommandError("Select an existing synthetic patient ID.")
        user_model = get_user_model()
        if (user_model.objects.filter(username=options["username"]).exists()
                or PatientPortalAccount.objects.filter(patient=patient).exists()):
            raise CommandError("The username or patient link already exists.")
        if not os.isatty(0):
            raise CommandError("Use an interactive terminal for the hidden password prompt.")
        user = user_model(username=options["username"])
        password = getpass.getpass("New synthetic portal password: ")
        try:
            user.full_clean(exclude=["password"])
            validate_password(password, user)
            with transaction.atomic():
                user.set_password(password)
                user.save(force_insert=True)
                PatientPortalAccount.objects.create(user=user, patient=patient)
                AuditEvent.objects.create(patient=patient, action="portal_account_provision",
                                          changed_fields=["patient_portal_account"])
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from None
        except IntegrityError:
            raise CommandError("The username or patient link already exists.") from None
        self.stdout.write(self.style.SUCCESS(f"Created linked synthetic portal account {user.username}."))
