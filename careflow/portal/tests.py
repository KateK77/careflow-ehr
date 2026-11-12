import secrets
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from careflow.history.models import MedicationStatement
from careflow.labs.test_review import ReviewFixture
from careflow.medications.services import transition_order
from careflow.medications.tests import MedicationFixture
from careflow.patients.models import AuditEvent
from .models import PatientPortalAccount, PatientVisibleResultRelease
from .records import release_result


class PortalFixture(ReviewFixture):
    def setup_portal(self):
        self.setup_review()
        self.password = secrets.token_urlsafe(24)
        user_model = get_user_model()
        self.portal_a = user_model.objects.create_user("portal-fixture-a", password=self.password)
        self.portal_b = user_model.objects.create_user("portal-fixture-b", password=self.password)
        PatientPortalAccount.objects.create(user=self.portal_a, patient=self.patient)
        PatientPortalAccount.objects.create(user=self.portal_b, patient=self.foreign)

    def release(self, result=None):
        return release_result(self.physician, (result or self.original).pk, self.physician.pk)


class PortalRecordTests(PortalFixture, TestCase):
    def setUp(self):
        self.setup_portal()

    def test_separate_login_logout_and_staff_boundary(self):
        url = reverse("portal_login")
        self.physician.set_password(self.password)
        self.physician.save(update_fields=["password"])
        denied = self.client.post(url, {"username": self.physician.username, "password": self.password})
        self.assertEqual(denied.status_code, 200)
        response = self.client.post(url, {"username": self.portal_a.username, "password": self.password, "next": "/app/"})
        self.assertRedirects(response, reverse("portal_home"))
        for path in ["/app/patients/", "/app/physician/", "/app/nursing/", "/app/pharmacy/", "/app/mar/",
                     "/app/portal/releases/"]:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.get(reverse("portal_logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("portal_logout")), url)
        self.assertRedirects(self.client.get(reverse("portal_home")), url + "?next=/portal/")
        staff_login = self.client.post(reverse("login"), {"username": self.portal_a.username, "password": self.password})
        self.assertContains(staff_login, "Use the patient portal sign-in")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_denied_and_csrf_applies_to_portal_actions(self):
        self.client.force_login(self.physician)
        self.assertEqual(self.client.get(reverse("portal_home")).status_code, 403)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.physician)
        self.assertEqual(protected.post(reverse("portal_releases"), {"result": self.original.pk, "confirm": "yes"}).status_code, 403)

    def test_owner_scope_no_soap_content(self):
        self.finish_encounter()
        self.client.force_login(self.portal_a)
        visits = self.client.get(reverse("portal_visits"))
        self.assertContains(visits, "No patient-facing visit summary has been published.")
        self.assertNotContains(visits, "Synthetic S")
        appointments = self.client.get(reverse("portal_appointments"))
        self.assertContains(appointments, "Arrived")
        self.assertContains(appointments, "Completed")
        self.client.force_login(self.portal_b)
        self.assertNotContains(self.client.get(reverse("portal_appointments")), "Arrived")
        self.assertNotContains(self.client.get(reverse("portal_home")), str(self.patient))

    def test_release_requires_ordering_physician_and_is_idempotent(self):
        with self.assertRaises(PermissionDenied):
            release_result(self.admin, self.original.pk, self.physician.pk)
        with self.assertRaises(ValidationError):
            release_result(self.other, self.original.pk, self.other.pk)
        self.assertEqual(self.release(), self.release())
        self.assertEqual(AuditEvent.objects.filter(action="portal_result_release").count(), 1)

    def test_acknowledgement_and_draft_do_not_release_values(self):
        self.acknowledge()
        self.action("correct", reason="Private draft correction")
        draft = self.order.results.get(status="draft")
        self.client.force_login(self.portal_a)
        for r in (self.original, draft):
            self.assertEqual(self.client.get(reverse("portal_result", args=[r.pk])).status_code, 404)
        self.assertContains(self.client.get(reverse("portal_results")), "No reports have been released")

    def test_release_only_own_current_revision_and_no_private_comments(self):
        self.release()
        corrected = self.correct()
        self.client.force_login(self.portal_a)
        for r in (self.original, corrected):
            self.assertEqual(self.client.get(reverse("portal_result", args=[r.pk])).status_code, 404)
        self.release(corrected)
        response = self.client.get(reverse("portal_result", args=[corrected.pk]))
        self.assertContains(response, "7.75")
        self.assertNotContains(response, "CORRECTED_SECRET")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.client.force_login(self.portal_b)
        self.assertEqual(self.client.get(reverse("portal_result", args=[corrected.pk])).status_code, 404)

    def test_context_error_withdrawal_blocks_old_released_values(self):
        self.release()
        self.action("withdraw", reason_code="context_error", reason="Private quarantine reason")
        self.client.force_login(self.portal_a)
        self.assertEqual(self.client.get(reverse("portal_result", args=[self.original.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("portal_results")), "Private quarantine reason")

    def test_report_error_withdrawal_blocks_old_released_values(self):
        self.release()
        self.action("withdraw", reason_code="report_error", reason="Private withdrawal reason")
        self.client.force_login(self.portal_a)
        self.assertEqual(self.client.get(reverse("portal_result", args=[self.original.pk])).status_code, 404)

    def test_audit_rollback(self):
        with patch("careflow.portal.records.AuditEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.release()
        self.assertFalse(PatientVisibleResultRelease.objects.exists())
class PortalMedicationTests(MedicationFixture, TestCase):
    def test_statement_signed_order_and_cancelled_order_are_distinct(self):
        self.setup_medications()
        user = get_user_model().objects.create_user("portal-medications")
        PatientPortalAccount.objects.create(user=user, patient=self.patient)
        MedicationStatement.objects.create(
            patient=self.patient, label="Synthetic historical statement", source="patient_reported",
            author=self.physician, updated_by=self.physician, dose="Historical dose",
            route="oral", frequency="daily", status="historical", comments="PRIVATE_STATEMENT_COMMENT",
        )
        self.make_order(dose="9 demo units")
        signed = self.sign(self.make_order())
        self.sign(self.make_order(dose="2 demo units"))
        transition_order(self.physician, signed.public_id, "cancel", signed.version, uuid.uuid4(),
                         True, reason="PRIVATE_CANCELLATION_REASON")
        self.client.force_login(user)
        response = self.client.get(reverse("portal_medications"))
        for value in ("Synthetic historical statement", "Historical", "Signed medication orders",
                      "2 demo units", "Cancelled"):
            self.assertContains(response, value)
        for value in ("9 demo units", "PRIVATE_STATEMENT_COMMENT", "PRIVATE_CANCELLATION_REASON"):
            self.assertNotContains(response, value)
