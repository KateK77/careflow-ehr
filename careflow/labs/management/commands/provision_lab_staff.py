import getpass
import os
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction


class Command(BaseCommand):
    help="Create a synthetic Lab Staff-only preview account without changing existing accounts."
    def add_arguments(self,parser): parser.add_argument('--username',required=True)
    def handle(self,*args,**options):
        target=Path(settings.DATABASES['default']['NAME']).resolve()
        if not os.environ.get('CAREFLOW_DB_PATH') or target==(settings.BASE_DIR/'db.sqlite3').resolve():
            raise CommandError('Select an explicit isolated preview with CAREFLOW_DB_PATH. Original database provisioning is not authorized.')
        username=options['username']
        if get_user_model().objects.filter(username=username).exists():
            raise CommandError('Account exists; no password or memberships changed.')
        password=os.environ.get('CAREFLOW_LAB_PASSWORD') or getpass.getpass('New synthetic Lab Staff password: ')
        user=get_user_model()(username=username)
        try: validate_password(password,user)
        except ValidationError as e: raise CommandError('; '.join(e.messages)) from None
        with transaction.atomic():
            user.set_password(password); user.save(); user.groups.add(Group.objects.get_or_create(name='Lab Staff')[0])
        self.stdout.write(self.style.SUCCESS('Created synthetic Lab Staff-only preview account. No password was logged.'))
