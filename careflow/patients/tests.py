import os
import secrets
from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import AuditEvent, Patient


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PatientManagementTests(TestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(24)
        self.staff = {}
        for role in ("Administrator", "Physician", "Nurse", "FrontDesk"):
            user = get_user_model().objects.create_user(role.lower(), password=self.password)
            user.groups.add(Group.objects.create(name=role))
            self.staff[role] = user
        self.outsider = get_user_model().objects.create_user("outsider", password=self.password)
        self.patient = Patient.objects.create(
            mrn="TEST-001", first_name="Avery", last_name="Synthetic",
            dob=date(1988, 4, 12), sex="unknown",
        )

    def sign_in(self, role="FrontDesk"):
        self.client.force_login(self.staff[role])

    def payload(self, **changes):
        values = {
            "mrn": "TEST-002", "first_name": "Jordan", "last_name": "Synthetic",
            "dob": "1992-06-20", "sex": "unknown", "phone": "", "email": "",
            "address": "", "gender_identity": "", "emergency_contact": "",
            "version": "1", "synthetic_only": "on",
        }
        values.update(changes)
        return values

    def test_login_and_logout_are_audited(self):
        response = self.client.post(reverse("login"), {
            "username": "frontdesk", "password": self.password,
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(AuditEvent.objects.filter(action="login", actor=self.staff["FrontDesk"]).exists())
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(AuditEvent.objects.filter(action="logout").exists())

    def test_bad_login_does_not_store_submitted_credentials(self):
        response = self.client.post(reverse("login"), {"username": "frontdesk", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(action="login_failed")
        self.assertEqual(event.outcome, "denied")
        self.assertIsNone(event.actor)

    def test_login_does_not_redirect_to_external_site(self):
        response = self.client.post(reverse("login"), {
            "username": "frontdesk", "password": self.password, "next": "https://example.invalid/",
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_all_four_roles_can_read(self):
        for role in self.staff:
            with self.subTest(role=role):
                self.sign_in(role)
                for name in ("dashboard", "patient_list"):
                    self.assertContains(self.client.get(reverse(name)), "DEMO — NOT FOR CLINICAL USE")
                self.assertContains(
                    self.client.get(reverse("patient_detail", args=[self.patient.pk])), "TEST-001",
                )

    def test_administrator_and_frontdesk_can_create_and_edit(self):
        for index, role in enumerate(("Administrator", "FrontDesk")):
            with self.subTest(role=role):
                self.sign_in(role)
                self.assertEqual(self.client.get(reverse("patient_create")).status_code, 200)
                data = self.payload(mrn=f"WRITER-{index}", first_name=f"Demo{index}")
                response = self.client.post(reverse("patient_create"), data)
                patient = Patient.objects.get(mrn=data["mrn"])
                self.assertRedirects(response, reverse("patient_detail", args=[patient.pk]))
                data["phone"] = "202-555-0100"
                response = self.client.post(reverse("patient_edit", args=[patient.pk]), data)
                self.assertEqual(response.status_code, 302)
                patient.refresh_from_db()
                self.assertEqual(patient.version, 2)
                self.assertEqual(patient.phone, "202-555-0100")

    def test_read_only_roles_cannot_write_by_direct_url(self):
        for role in ("Physician", "Nurse"):
            with self.subTest(role=role):
                self.sign_in(role)
                self.assertNotContains(self.client.get(reverse("patient_list")), "＋ Register patient")
                for name, args in (("patient_create", []), ("patient_edit", [self.patient.pk])):
                    self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403)
                    self.assertEqual(self.client.post(reverse(name, args=args), self.payload()).status_code, 403)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertTrue(AuditEvent.objects.filter(action="access_denied", outcome="denied").exists())

    def test_anonymous_requests_are_redirected_and_audited(self):
        self.assertRedirects(
            self.client.get(reverse("patient_list")),
            reverse("login") + "?next=" + reverse("patient_list"),
        )
        self.assertEqual(self.client.post(reverse("patient_create"), self.payload()).status_code, 302)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="access_denied").count(), 2)

    def test_user_with_no_staff_role_is_denied(self):
        self.client.force_login(self.outsider)
        for url in (reverse("dashboard"), reverse("patient_list"), reverse("patient_detail", args=[self.patient.pk])):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_creation_persists_and_records_actor_and_fields(self):
        self.sign_in()
        self.client.post(reverse("patient_create"), self.payload(mrn="test-002"))
        patient = Patient.objects.get(mrn="TEST-002")
        event = AuditEvent.objects.get(action="patient_create")
        self.assertEqual(event.patient_id, patient.pk)
        self.assertEqual(event.actor, self.staff["FrontDesk"])
        self.assertIn("dob", event.changed_fields)
        self.assertNotIn("Jordan", event.changed_fields)
        self.assertContains(self.client.get(reverse("patient_detail", args=[patient.pk])), "Jordan")

    def test_edit_records_changed_fields_and_version(self):
        self.sign_in()
        data = self.payload(mrn="TEST-001", first_name="Avery", dob="1988-04-12", phone="555-0101")
        self.client.post(reverse("patient_edit", args=[self.patient.pk]), data)
        event = AuditEvent.objects.get(action="patient_update")
        self.assertEqual(event.changed_fields, ["phone"])
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.version, 2)

    def test_stale_editor_cannot_overwrite_newer_change(self):
        self.sign_in()
        url = reverse("patient_edit", args=[self.patient.pk])
        self.client.post(url, self.payload(mrn="TEST-001", phone="555-0101"))
        response = self.client.post(url, self.payload(mrn="TEST-001", phone="555-0102"))
        self.assertContains(response, "record changed", status_code=409)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.phone, "555-0101")
        self.assertEqual(AuditEvent.objects.filter(action="patient_update").count(), 1)

    def test_missing_edit_version_is_invalid(self):
        self.sign_in()
        data = self.payload(mrn="TEST-001")
        del data["version"]
        response = self.client.post(reverse("patient_edit", args=[self.patient.pk]), data)
        self.assertIn("version", response.context["form"].errors)
        self.assertFalse(AuditEvent.objects.filter(action="patient_update").exists())

    def test_duplicate_mrn_is_case_insensitive(self):
        self.sign_in()
        response = self.client.post(reverse("patient_create"), self.payload(mrn="test-001"))
        self.assertContains(response, "MRN already exists")
        self.assertEqual(Patient.objects.count(), 1)

    def test_database_rejects_case_variant_mrn(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Patient.objects.create(
                mrn="test-001", first_name="Other", last_name="Demo",
                dob=date(2000, 1, 1), sex="unknown",
            )

    def test_duplicate_identity_requires_explicit_confirmation(self):
        self.sign_in()
        data = self.payload(first_name="avery", last_name="Synthetic", dob="1988-04-12")
        response = self.client.post(reverse("patient_create"), data)
        self.assertContains(response, "Potential duplicate")
        self.assertContains(response, 'name="confirm_duplicate"')
        self.assertEqual(Patient.objects.count(), 1)
        data["confirm_duplicate"] = "on"
        self.assertEqual(self.client.post(reverse("patient_create"), data).status_code, 302)
        self.assertEqual(Patient.objects.count(), 2)

    def test_editing_same_identity_does_not_flag_itself(self):
        self.sign_in()
        data = self.payload(mrn="TEST-001", first_name="Avery", dob="1988-04-12")
        self.assertEqual(self.client.post(reverse("patient_edit", args=[self.patient.pk]), data).status_code, 302)

    def test_invalid_inputs_are_rejected(self):
        self.sign_in()
        cases = [
            {"dob": (timezone.localdate() + timedelta(days=1)).isoformat()},
            {"dob": "not-a-date"}, {"email": "invalid"}, {"first_name": " "},
            {"mrn": "BAD MRN"}, {"sex": "invalid"}, {"sex": ""}, {"phone": "letters"},
            {"synthetic_only": ""},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post(reverse("patient_create"), self.payload(**changes))
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(Patient.objects.count(), 1)

    def test_empty_submission_displays_errors(self):
        self.sign_in()
        response = self.client.post(reverse("patient_create"), {})
        self.assertTrue(response.context["form"].errors)

    def test_search_by_name_mrn_dob_and_phone(self):
        self.sign_in()
        self.patient.phone = "202-555-0199"
        self.patient.save()
        for query in ("Avery", "Avery Synthetic", "test-001", "1988-04-12", "0199"):
            with self.subTest(query=query):
                response = self.client.get(reverse("patient_list"), {"q": query})
                self.assertContains(response, "TEST-001")
        self.assertContains(self.client.get(reverse("patient_list"), {"q": "no-match"}), "No patients match")

    def test_filter_and_pagination(self):
        self.sign_in()
        for i in range(16):
            Patient.objects.create(
                mrn=f"PAGE-{i}", first_name=f"Demo{i}", last_name="Synthetic",
                dob=date(2000, 1, 1), sex="female",
            )
        response = self.client.get(reverse("patient_list"), {"sex": "female"})
        self.assertEqual(response.context["page"].paginator.count, 16)
        self.assertEqual(len(response.context["page"]), 15)
        response = self.client.get(reverse("patient_list"), {"sex": "female", "page": "2"})
        self.assertEqual(len(response.context["page"]), 1)
        self.assertEqual(self.client.get(reverse("patient_list"), {"page": "bad"}).status_code, 200)

    def test_missing_patient_returns_404(self):
        self.sign_in()
        self.assertEqual(self.client.get(reverse("patient_detail", args=[99999])).status_code, 404)

    def test_get_never_saves_patient(self):
        self.sign_in()
        for url in (reverse("patient_create"), reverse("patient_edit", args=[self.patient.pk])):
            self.assertContains(self.client.get(url), "synthetic")
        self.assertFalse(AuditEvent.objects.filter(action__in=["patient_create", "patient_update"]).exists())

    def test_audit_failure_rolls_back_patient_creation(self):
        self.sign_in()
        with patch("careflow.patients.views.AuditEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse("patient_create"), self.payload())
        self.assertEqual(Patient.objects.count(), 1)

    def test_audit_failure_rolls_back_patient_edit(self):
        self.sign_in()
        with patch("careflow.patients.views.AuditEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("patient_edit", args=[self.patient.pk]),
                    self.payload(mrn="TEST-001", phone="555-0101"),
                )
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.phone, "")
        self.assertEqual(self.patient.version, 1)

    def test_post_requires_csrf_token(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.staff["FrontDesk"])
        self.assertEqual(secure.post(reverse("patient_create"), self.payload()).status_code, 403)
        self.assertEqual(Patient.objects.count(), 1)

    def test_saved_html_is_escaped(self):
        self.sign_in()
        self.patient.address = "<script>alert(1)</script>"
        self.patient.save()
        response = self.client.get(reverse("patient_detail", args=[self.patient.pk]))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>")

    def test_detail_is_patient_scoped(self):
        self.sign_in()
        other = Patient.objects.create(
            mrn="OTHER", first_name="UniqueOther", last_name="Synthetic",
            dob=date(2001, 1, 1), sex="unknown",
        )
        response = self.client.get(reverse("patient_detail", args=[self.patient.pk]))
        self.assertNotContains(response, other.mrn)
        self.assertNotContains(response, other.first_name)


class SyntheticSeedTests(TestCase):
    @override_settings(DEBUG=True)
    def test_seed_is_repeatable_and_preserves_changes_and_passwords(self):
        password = secrets.token_urlsafe(24)
        with patch.dict(os.environ, {"CAREFLOW_ALLOW_DEMO_SEED": "1", "CAREFLOW_DEMO_PASSWORD": password}):
            call_command("seed_synthetic", stdout=StringIO())
            first = Patient.objects.get(mrn="DEMO-0001")
            first.phone = "555-0111"
            first.save()
            user = get_user_model().objects.get(username="frontdesk.demo")
            original_hash = user.password
            with patch.dict(os.environ, {"CAREFLOW_DEMO_PASSWORD": secrets.token_urlsafe(24)}):
                call_command("seed_synthetic", stdout=StringIO())
        self.assertEqual(Patient.objects.count(), 30)
        self.assertEqual(get_user_model().objects.count(), 4)
        first.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(first.phone, "555-0111")
        self.assertEqual(user.password, original_hash)
        self.assertEqual(AuditEvent.objects.filter(action="patient_seed").count(), 30)

    @override_settings(DEBUG=True)
    def test_seed_requires_explicit_opt_in(self):
        with patch.dict(os.environ, {"CAREFLOW_ALLOW_DEMO_SEED": "0"}):
            with self.assertRaises(CommandError):
                call_command("seed_synthetic", stdout=StringIO())
        self.assertEqual(Patient.objects.count(), 0)

    @override_settings(DEBUG=True)
    def test_weak_or_missing_password_rolls_back_seed(self):
        for password in ("", "123"):
            with patch.dict(os.environ, {"CAREFLOW_ALLOW_DEMO_SEED": "1", "CAREFLOW_DEMO_PASSWORD": password}):
                with self.assertRaises(CommandError):
                    call_command("seed_synthetic", stdout=StringIO())
                self.assertEqual(get_user_model().objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_seed_disabled_outside_debug(self):
        with patch.dict(os.environ, {"CAREFLOW_ALLOW_DEMO_SEED": "1"}):
            with self.assertRaises(CommandError):
                call_command("seed_synthetic", stdout=StringIO())

    @override_settings(DEBUG=True)
    def test_seed_refuses_existing_unrelated_demo_username(self):
        get_user_model().objects.create_user("physician.demo")
        with patch.dict(os.environ, {
            "CAREFLOW_ALLOW_DEMO_SEED": "1", "CAREFLOW_DEMO_PASSWORD": secrets.token_urlsafe(24),
        }):
            with self.assertRaises(CommandError):
                call_command("seed_synthetic", stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Patient.objects.count(), 0)
