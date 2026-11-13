"""Presentation regressions on isolated Django test databases."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientPortalAccount
from careflow.scheduling.models import Appointment, AppointmentEvent
from careflow.history import test_uat


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class WorkspaceUpgradeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = {}
        for role in ("FrontDesk", "Physician", "Nurse", "Administrator", "Lab Staff"):
            actor = get_user_model().objects.create_user(username="upgrade-" + role)
            actor.groups.add(Group.objects.get_or_create(name=role)[0])
            cls.staff[role] = actor
        cls.patient = Patient.objects.create(
            mrn="SYN-UPGRADE", first_name="Synthetic", last_name="Workspace",
            dob=date(1990, 1, 1), sex="unknown",
        )

    def test_frontdesk_dashboard_does_not_offer_clinical_workspaces(self):
        self.client.force_login(self.staff["FrontDesk"])
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "View patient directory")
        self.assertContains(response, "View arrivals worklist")
        for name in ("physician_workspace", "nursing_workspace", "lab_worklist"):
            self.assertNotContains(response, 'href="' + reverse(name) + '"')
        self.assertEqual(self.client.get(reverse("physician_workspace")).status_code, 403)

    def test_physician_dashboard_preserves_read_only_demographics(self):
        self.client.force_login(self.staff["Physician"])
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Open clinical workspace")
        self.assertNotContains(response, 'href="' + reverse("patient_create") + '"')
        self.assertEqual(self.client.get(reverse("patient_create")).status_code, 403)
        self.assertEqual(self.client.post(reverse("patient_edit", args=[self.patient.pk]), {}).status_code, 403)

    def test_lab_identity_and_brand_link_target_own_workspace(self):
        self.client.force_login(self.staff["Lab Staff"])
        response = self.client.get(reverse("lab_worklist"))
        self.assertContains(response, "Lab Staff")
        self.assertNotContains(response, "No staff role")
        self.assertContains(response, 'href="' + reverse("lab_worklist") + '"')
        self.assertNotContains(response, 'href="' + reverse("dashboard") + '"')
        self.assertEqual(self.client.get(reverse("patient_list")).status_code, 403)
        self.staff["Lab Staff"].groups.add(Group.objects.get_or_create(name="Pharmacist")[0])
        self.assertContains(self.client.get(reverse("lab_worklist")), "Pharmacist · Lab Staff")

    def test_anonymous_login_links_back_to_portal_selection(self):
        for route in ("login", "portal_login"):
            response = self.client.get(reverse(route))
            self.assertContains(response, 'href="' + reverse("home") + '"')
            self.assertContains(response, "Back to portal selection")
            self.assertContains(response, "DEMO — NOT FOR CLINICAL USE")

    def test_patient_account_stays_outside_staff_workspace(self):
        actor = get_user_model().objects.create_user(username="upgrade-portal")
        PatientPortalAccount.objects.create(user=actor, patient=self.patient)
        self.client.force_login(actor)
        self.assertContains(self.client.get(reverse("portal_home")), str(self.patient))
        response = self.client.get(reverse("patient_list"))
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, self.patient.mrn, status_code=403)

    def test_patient_directory_action_and_readable_audit_preserve_storage(self):
        actor = self.staff["FrontDesk"]
        event = AuditEvent.objects.create(actor=actor, patient=self.patient, action="patient_create",
                                         changed_fields=["mrn", "dob", "first_name"])
        self.client.force_login(actor)
        self.assertContains(self.client.get(reverse("patient_list")), "View Patient")
        response = self.client.get(reverse("patient_detail", args=[self.patient.pk]))
        self.assertContains(response, "Patient registered")
        self.assertContains(response, actor.username)
        self.assertContains(response, "MRN, Date of birth, First name")
        self.assertNotContains(response, "<strong>patient_create</strong>", html=True)
        event.refresh_from_db()
        self.assertEqual(event.action, "patient_create")
        self.assertEqual(event.changed_fields, ["mrn", "dob", "first_name"])

    def test_appointment_search_opens_only_with_query_and_never_writes(self):
        self.client.force_login(self.staff["FrontDesk"])
        url = reverse("appointment_create")
        response = self.client.get(url)
        self.assertContains(response, '<details class="panel appointment-search">')
        self.assertNotContains(response, '<details class="panel appointment-search" open>')
        response = self.client.get(url, {"q": self.patient.mrn})
        self.assertContains(response, '<details class="panel appointment-search" open>')
        self.assertContains(response, 'value="' + self.patient.mrn + '"')
        self.assertFalse(Appointment.objects.exists())

    def test_appointment_history_wraps_reason_and_preserves_event_values(self):
        now = timezone.now()
        appointment = Appointment.objects.create(
            patient=self.patient, physician=self.staff["Physician"], start_at=now,
            end_at=now + timedelta(minutes=30), appointment_type="Synthetic",
        )
        audit = AuditEvent.objects.create(actor=self.staff["FrontDesk"], patient=self.patient,
                                         action="appointment_create")
        event = AppointmentEvent.objects.create(appointment=appointment, audit=audit,
                                               previous_status="", next_status="scheduled", reason="Synthetic reason")
        self.client.force_login(self.staff["FrontDesk"])
        response = self.client.get(reverse("appointment_detail", args=[appointment.pk]))
        self.assertContains(response, "Appointment booked")
        self.assertContains(response, 'class="clinical-table appointment-history"')
        event.refresh_from_db()
        self.assertEqual(event.next_status, "scheduled")
        self.assertEqual(event.reason, "Synthetic reason")


class AllergyErrorPresentationTests(TestCase):
    setUpTestData = classmethod(test_uat.UATValidationTests.setUpTestData.__func__)
    setUp = test_uat.UATValidationTests.setUp
    data = test_uat.UATValidationTests.data
    payload = test_uat.UATValidationTests.payload
    save = test_uat.UATValidationTests.save
    url = test_uat.UATValidationTests.url

    def test_conflict_message_once_and_submitted_confirmation_preserved(self):
        from careflow.history.models import AllergyState
        self.save("allergies")
        state = AllergyState.objects.get(patient=self.patient)
        response = self.client.post(reverse("allergy_state_review", args=[self.patient.pk]),
                                    {"version": state.version, "status": "no_known", "synthetic_confirmed": "on"})
        self.assertContains(response, "The allergy assessment conflicts", count=1, status_code=400)
        self.assertContains(response, 'value="no_known" selected', status_code=400)
        self.assertContains(response, "checked", status_code=400)
        self.assertNotContains(response, "__all__", status_code=400)
        state.refresh_from_db()
        self.assertEqual(state.status, "documented")

    def test_field_errors_once_and_confirmation_not_automatically_checked(self):
        response = self.client.post(reverse("allergy_state_review", args=[self.patient.pk]),
                                    {"version": 0, "status": "unknown"})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "This field is required.", count=1, status_code=400)
        self.assertNotContains(response, " checked", status_code=400)
