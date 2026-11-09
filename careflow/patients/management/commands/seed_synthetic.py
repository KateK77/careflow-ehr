import os
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from careflow.patients.access import READ_ROLES
from careflow.patients.models import AuditEvent, Patient


class Command(BaseCommand):
    help = "Create synthetic patients and four demo staff accounts without resetting existing data."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG or os.environ.get("CAREFLOW_ALLOW_DEMO_SEED") != "1":
            raise CommandError("Set CAREFLOW_ALLOW_DEMO_SEED=1 in a local development environment.")
        users = get_user_model()
        password = os.environ.get("CAREFLOW_DEMO_PASSWORD", "")
        for role in READ_ROLES:
            username = f"{role.lower()}.demo"
            email = f"{role.lower()}@example.invalid"
            user = users.objects.filter(username=username).first()
            if user is not None:
                if user.email != email or user.first_name != "Synthetic" or user.last_name != role:
                    raise CommandError(f"Existing account conflicts with reserved demo username {username}.")
                continue
            user = users(username=username, email=email, first_name="Synthetic", last_name=role)
            if not password:
                raise CommandError("Set CAREFLOW_DEMO_PASSWORD for new accounts. Existing passwords are preserved.")
            try:
                validate_password(password, user)
            except ValidationError as error:
                raise CommandError("Demo password does not meet the configured password policy.") from error
            user.set_password(password)
            user.save()
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
        for index in range(1, 31):
            mrn = f"DEMO-{index:04d}"
            patient, created = Patient.objects.get_or_create(
                mrn=mrn,
                defaults={
                    "first_name": f"Demo{index:02d}", "last_name": "Synthetic",
                    "dob": date(1970 + index, index % 12 + 1, index % 25 + 1),
                    "sex": Patient.Sex.FEMALE if index % 2 else Patient.Sex.MALE,
                    "email": f"patient{index:02d}@example.invalid",
                },
            )
            if created:
                AuditEvent.objects.create(patient=patient, action="patient_seed")
        self.stdout.write(self.style.SUCCESS("Synthetic seed complete. Existing records and passwords were preserved."))
