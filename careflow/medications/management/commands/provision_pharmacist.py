import getpass
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from careflow.medications.models import PharmacyReview


class Command(BaseCommand):
    help = "Create a new synthetic Pharmacist account in a Phase 4A preview."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--confirm-preview", action="store_true", required=True)

    def handle(self, *args, **options):
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if (not os.environ.get("CAREFLOW_DB_PATH") or not target.is_file()
                or target == (settings.BASE_DIR / "db.sqlite3").resolve()):
            raise CommandError("Select a separate migrated Phase 4A preview through CAREFLOW_DB_PATH.")
        if PharmacyReview._meta.db_table not in connection.introspection.table_names():
            raise CommandError("The selected database has no pharmacy tables.")
        user_model = get_user_model()
        username = options["username"]
        if user_model.objects.filter(username=username).exists():
            raise CommandError("That account already exists.")
        user = user_model(username=username)
        password = getpass.getpass("New synthetic Pharmacist password: ")
        try:
            user.full_clean(exclude=["password"])
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from None
        with transaction.atomic():
            user.set_password(password)
            user.save()
            user.groups.add(Group.objects.get_or_create(name="Pharmacist")[0])
        self.stdout.write(self.style.SUCCESS("Created a synthetic Pharmacist-only account."))
