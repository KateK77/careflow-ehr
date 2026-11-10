from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
import os


class Command(BaseCommand):
    help='Explicitly grant narrow laboratory review permissions to an existing Administrator in an isolated preview.'
    def add_arguments(self,parser):
        parser.add_argument('--username',required=True)
        parser.add_argument('--reassign-review',action='store_true')
        parser.add_argument('--inspect-quarantine',action='store_true')
        parser.add_argument('--confirm-preview',action='store_true')
    def handle(self,*args,**options):
        if not options['confirm_preview'] or not os.environ.get('CAREFLOW_DB_PATH') or Path(settings.DATABASES['default']['NAME']).resolve()==(settings.BASE_DIR/'db.sqlite3').resolve():
            raise CommandError('Explicitly select and confirm an isolated preview. Original database writes are not authorized.')
        user=get_user_model().objects.filter(username=options['username'],is_active=True,groups__name='Administrator').first()
        if not user: raise CommandError('Choose an existing active Administrator account.')
        codes=[]
        if options['reassign_review']:codes.append('reassign_review_responsibility')
        if options['inspect_quarantine']:codes.append('view_quarantined_report')
        if not codes:raise CommandError('Choose explicit capabilities; no global or implicit grants are made.')
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label='labs',codename__in=codes))
        self.stdout.write(self.style.SUCCESS('Explicit preview-only laboratory capabilities granted. No role or password changed.'))
