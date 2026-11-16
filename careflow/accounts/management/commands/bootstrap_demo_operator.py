"""Trusted operator bootstrap; never exposed as a public registration role."""
import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from careflow.accounts.forms import username_validator
from django.db import transaction
from django.utils import timezone
from careflow.accounts.models import Enrollment, AccountEvent


class Command(BaseCommand):
    help = "Create the first operator in a newly provisioned synthetic demo database."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--confirm-synthetic", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm_synthetic"]:
            raise CommandError("Confirm this is an isolated synthetic demo.")
        users = get_user_model()
        if users.objects.filter(groups__name="Administrator").exists():
            raise CommandError("An Administrator already exists. No account was changed.")
        username = options["username"]
        try:
            username_validator(username)
        except ValidationError as error:
            raise CommandError("Enter a valid lowercase operator username.") from error
        if users.objects.filter(username__iexact=username).exists():
            raise CommandError("An account already uses this username. No account was changed.")
        password = getpass.getpass("New operator password (hidden): ")
        if password != getpass.getpass("Confirm password (hidden): "):
            raise CommandError("Passwords do not match.")
        user = users(username=username,
                     first_name="Demo", last_name="Operator", is_active=True)
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError("Password does not meet the configured policy.") from error
        user.set_password(password)
        user.save()
        user.groups.add(Group.objects.get_or_create(name="Administrator")[0])
        item = Enrollment.objects.create(user=user, kind="staff", status="approved",
            reviewed_at=timezone.now(), reviewed_by=user,
            granted_role="Administrator", review_reason="Trusted console bootstrap by the hosting owner.")
        AccountEvent.objects.create(enrollment=item, actor=user, action="operator_bootstrap",
                                    role="Administrator", reason=item.review_reason)
        self.stdout.write("First operator created. Sign in using the supplied username. No superuser access was granted.")
