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

from careflow.hospital.models import EmergencyVisit
from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientPortalAccount


ROLES = ("Administrator", "Physician", "Nurse", "RadiologyStaff", "BillingStaff", "HospitalOperations", "PatientPortal")


class Command(BaseCommand):
    help = "Create a new synthetic role-specific account in the final Phase 8 preview."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--role", choices=ROLES, required=True)
        parser.add_argument("--patient-id", type=int)
        parser.add_argument("--confirm-preview", action="store_true", required=True)

    def handle(self, *args, **options):
        configured = Path(settings.DATABASES["default"]["NAME"])
        preview = (settings.BASE_DIR / ".venv").resolve() / "phase8-final-preview.sqlite3"
        if (not os.environ.get("CAREFLOW_DB_PATH") or configured.resolve() != preview
                or not preview.is_file() or preview.is_symlink()):
            raise CommandError("Select the existing final Phase 8 preview database.")
        if EmergencyVisit._meta.db_table not in connection.introspection.table_names():
            raise CommandError("The final Phase 8 preview schema is required.")
        role, patient_id = options["role"], options["patient_id"]
        if (role == "PatientPortal") != (patient_id is not None):
            raise CommandError("Provide a synthetic patient ID only for PatientPortal accounts.")
        patient = None
        if patient_id is not None:
            patient = Patient.objects.filter(pk=patient_id).first()
            if patient is None or PatientPortalAccount.objects.filter(patient=patient).exists():
                raise CommandError("Choose an existing synthetic patient without a portal account.")
        user_model = get_user_model()
        user = user_model(username=options["username"])
        if user_model.objects.filter(username=user.username).exists():
            raise CommandError("This username already exists.")
        if not os.isatty(0):
            raise CommandError("Use an interactive terminal for the hidden password prompt.")
        password = getpass.getpass("New synthetic account password: ")
        try:
            user.full_clean(exclude=["password"])
            validate_password(password, user)
            with transaction.atomic():
                user.set_password(password)
                user.save(force_insert=True)
                if patient:
                    PatientPortalAccount.objects.create(patient=patient, user=user)
                else:
                    group, _ = Group.objects.get_or_create(name=role)
                    user.groups.add(group)
                AuditEvent.objects.create(patient=patient, action="integrated_account_provision",
                                          changed_fields=["user", "role" if not patient else "patient_portal_account"])
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from None
        except IntegrityError:
            raise CommandError("The username or patient link already exists.") from None
        self.stdout.write(self.style.SUCCESS(f"Created {user.username} for {role}."))
