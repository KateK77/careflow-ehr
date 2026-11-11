import os,secrets
from unittest.mock import patch
from io import StringIO
from django.test import TestCase,override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class LabProvisioningTests(TestCase):
    def test_default_database_selection_is_refused(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(CommandError):call_command('provision_lab_staff',username='preview.lab',stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username='preview.lab').exists())

    def test_preview_account_has_only_lab_role_and_no_password_output(self):
        password=secrets.token_urlsafe(24);out=StringIO()
        with patch.dict(os.environ,{'CAREFLOW_DB_PATH':'isolated-test-preview','CAREFLOW_LAB_PASSWORD':password}):
            call_command('provision_lab_staff',username='preview.lab',stdout=out)
            with self.assertRaises(CommandError):call_command('provision_lab_staff',username='preview.lab',stdout=out)
        user=get_user_model().objects.get(username='preview.lab');self.assertTrue(user.check_password(password));self.assertEqual(list(user.groups.values_list('name',flat=True)),['Lab Staff']);self.assertNotIn(password,out.getvalue())
        self.client.force_login(user);self.assertEqual(self.client.get('/app/lab/workspace/').status_code,200);self.assertEqual(self.client.get('/app/patients/').status_code,403)

    def test_permission_grants_require_explicit_preview_and_administrator(self):
        user=get_user_model().objects.create_user('preview.admin');user.groups.add(Group.objects.get_or_create(name='Administrator')[0]);out=StringIO()
        with patch.dict(os.environ,{'CAREFLOW_DB_PATH':'isolated-test-preview'}):
            with self.assertRaises(CommandError):call_command('grant_lab_preview_permissions',username=user.username,reassign_review=True,stdout=out)
            call_command('grant_lab_preview_permissions',username=user.username,reassign_review=True,confirm_preview=True,stdout=out)
        self.assertEqual(list(user.user_permissions.values_list('codename',flat=True)),['reassign_review_responsibility'])

    def test_default_grant_refuses_without_changing_permissions(self):
        user=get_user_model().objects.create_user('restricted.account')
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(CommandError):call_command('grant_lab_preview_permissions',username=user.username,reassign_review=True,confirm_preview=True,stdout=StringIO())
        self.assertFalse(user.user_permissions.exists())
