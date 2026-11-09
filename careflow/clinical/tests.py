from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from careflow.patients.models import AuditEvent, Patient
from careflow.scheduling.models import Appointment, AppointmentEvent
from careflow.scheduling.services import AppointmentConflict, transition_appointment
from .models import ClinicalEvent, Encounter, Note
from .services import ClinicalConflict, complete_encounter, save_note, sign_note, start_encounter


class ClinicalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {}
        for role in ["Administrator", "Physician", "Nurse", "FrontDesk"]:
            user = get_user_model().objects.create_user(username=role.lower())
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            cls.users[role] = user
        cls.physician = cls.users["Physician"]
        cls.other = get_user_model().objects.create_user(username="other-physician")
        cls.other.groups.add(Group.objects.get(name="Physician"))
        cls.patient = Patient.objects.create(mrn="CLINICAL-1", first_name="Synthetic", last_name="Chart",
                                             dob=date(1980, 1, 1), sex="unknown")
        cls.unrelated = Patient.objects.create(mrn="CLINICAL-2", first_name="Fictional", last_name="Other",
                                               dob=date(1990, 2, 2), sex="female")

    def setUp(self):
        now = timezone.now()
        self.appointment = Appointment.objects.create(patient=self.patient, physician=self.physician,
            start_at=now, end_at=now + timedelta(minutes=30), appointment_type="Synthetic visit",
            status="arrived", checked_in_at=now, checked_in_by=self.users["FrontDesk"])
        self.client.force_login(self.physician)

    def start(self):
        return start_encounter(self.physician, self.appointment.pk, 1)

    def data(self, **changes):
        return {"subjective": "Fictional symptom", "objective": "Synthetic observations",
                "assessment": "Fictional assessment for testing", "plan": "Synthetic plan only",
                "synthetic_confirmed": True, **changes}

    def note(self, encounter=None):
        return save_note(self.physician, (encounter or self.start()).pk, self.data(), 0)

    def url(self, name, encounter, *extra):
        return reverse(name, args=[encounter.patient_id, encounter.pk, *extra])

    def test_chart_scope_and_read_audit(self):
        response = self.client.get(reverse("patient_chart", args=[self.patient.pk]))
        self.assertContains(response, self.patient.mrn)
        self.assertTrue(AuditEvent.objects.filter(action="chart_view", patient=self.patient).exists())
        self.assertEqual(self.client.get(reverse("patient_chart", args=[self.unrelated.pk])).status_code, 404)

    def test_frontdesk_clinical_denial_without_note_leakage(self):
        note = self.note()
        self.client.force_login(self.users["FrontDesk"])
        for name, args in [("patient_chart", [self.patient.pk]), ("physician_workspace", []),
                           ("encounter_detail", [self.patient.pk, note.encounter_id])]:
            for method in [self.client.get, self.client.post]:
                response = method(reverse(name, args=args))
                self.assertIn(response.status_code, [403, 405])
                self.assertNotIn(note.subjective, response.content.decode())
        self.assertTrue(AuditEvent.objects.filter(action="clinical_access_denied", outcome="denied").exists())

    def test_administrator_and_nurse_read_but_cannot_author(self):
        encounter = self.start()
        note = self.note(encounter)
        for role in ["Administrator", "Nurse"]:
            self.client.force_login(self.users[role])
            self.assertContains(self.client.get(self.url("encounter_detail", encounter)), note.subjective)
            for name, extra in [("note_edit", []), ("note_sign", [note.pk]), ("encounter_complete", [])]:
                self.assertEqual(self.client.post(self.url(name, encounter, *extra), self.data(version=1, confirmed=True)).status_code, 403)

    def test_other_physician_isolation(self):
        encounter = self.start()
        note = self.note(encounter)
        self.client.force_login(self.other)
        for name, extra in [("encounter_detail", []), ("note_edit", []), ("note_sign", [note.pk])]:
            self.assertEqual(self.client.get(self.url(name, encounter, *extra)).status_code, 404)
            self.assertIn(self.client.post(self.url(name, encounter, *extra), self.data(version=1)).status_code, [404, 405])

    def test_workspace_scopes_appointments_and_encounters(self):
        self.start()
        response = self.client.get(reverse("physician_workspace"))
        self.assertContains(response, self.patient.mrn)
        self.assertContains(response, "In progress")
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("physician_workspace")), self.patient.mrn)

    def test_invalid_workspace_date(self):
        self.assertContains(self.client.get(reverse("physician_workspace"), {"date": "invalid"}), "Enter a valid date")

    def test_explicit_start_preserves_appointment(self):
        before = Appointment.objects.values().get(pk=self.appointment.pk)
        self.assertFalse(Encounter.objects.exists())
        encounter = self.start()
        self.assertEqual(Appointment.objects.values().get(pk=self.appointment.pk), before)
        self.assertEqual(encounter.patient, self.patient)
        self.assertEqual(encounter.status, "in_progress")
        self.assertIsNotNone(encounter.started_at)
        self.assertTrue(encounter.events.filter(audit__action="encounter_start").exists())

    def test_duplicate_start_service_and_database(self):
        self.start()
        with self.assertRaises(ClinicalConflict):
            self.start()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Encounter.objects.create(appointment=self.appointment, patient=self.patient, physician=self.physician)
        self.assertEqual(Encounter.objects.count(), 1)

    def test_start_requires_arrived_and_current_version(self):
        for status in ["scheduled", "cancelled", "no_show"]:
            Appointment.objects.filter(pk=self.appointment.pk).update(status=status)
            with self.assertRaises(ClinicalConflict):
                self.start()
        Appointment.objects.filter(pk=self.appointment.pk).update(status="arrived", version=2)
        with self.assertRaises(ClinicalConflict):
            self.start()
        self.assertFalse(Encounter.objects.exists())

    def test_start_and_mutations_require_owner(self):
        for actor in [self.other, self.users["Administrator"], self.users["Nurse"], self.users["FrontDesk"]]:
            with self.assertRaises(PermissionDenied):
                start_encounter(actor, self.appointment.pk, 1)
        encounter = self.start()
        note = self.note(encounter)
        with self.assertRaises(PermissionDenied):
            save_note(self.other, encounter.pk, self.data(), 1)
        with self.assertRaises(PermissionDenied):
            sign_note(self.other, note.pk, 1, True)
        with self.assertRaises(PermissionDenied):
            complete_encounter(self.other, encounter.pk, 1)

    def test_start_get_is_nonmutating_post_persists(self):
        url = reverse("encounter_start", args=[self.appointment.pk])
        self.assertContains(self.client.get(url), "Confirm encounter start")
        self.assertFalse(Encounter.objects.exists())
        self.assertEqual(self.client.post(url, {"version": 1}).status_code, 302)
        self.assertEqual(Encounter.objects.count(), 1)
        self.assertEqual(self.client.post(url, {"version": 1}).status_code, 409)

    def test_draft_creation_edit_and_reopen(self):
        encounter = self.start()
        url = self.url("note_edit", encounter)
        response = self.client.post(url, self.data(version=0))
        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(encounter=encounter)
        self.assertContains(self.client.get(url), "Fictional symptom")
        self.client.post(url, self.data(version=1, subjective="Updated fictional symptom"))
        note.refresh_from_db()
        self.assertEqual(note.subjective, "Updated fictional symptom")
        self.assertEqual(note.version, 2)
        self.assertEqual(note.author, self.physician)
        self.assertEqual(list(encounter.events.values_list("audit__action", flat=True)), ["note_edit", "note_create", "encounter_start"])

    def test_drafts_allow_incomplete_but_signing_does_not(self):
        encounter = self.start()
        note = save_note(self.physician, encounter.pk, self.data(plan=""), 0)
        with self.assertRaises(ValidationError):
            sign_note(self.physician, note.pk, 1, True)
        note.refresh_from_db()
        self.assertIsNone(note.signed_at)

    def test_draft_requires_synthetic_confirmation_and_limits(self):
        encounter = self.start()
        response = self.client.post(self.url("note_edit", encounter), self.data(version=0, synthetic_confirmed=""))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Fictional symptom", status_code=400)
        self.assertFalse(Note.objects.exists())
        with self.assertRaises(ValidationError):
            save_note(self.physician, encounter.pk, self.data(subjective="x" * 20001), 0)
        self.assertFalse(Note.objects.exists())

    def test_stale_draft_and_duplicate_creation_rejected(self):
        encounter = self.start()
        note = self.note(encounter)
        with self.assertRaises(ClinicalConflict):
            save_note(self.physician, encounter.pk, self.data(subjective="Stale"), 0)
        save_note(self.physician, encounter.pk, self.data(subjective="New"), 1)
        with self.assertRaises(ClinicalConflict):
            sign_note(self.physician, note.pk, 1, True)
        note.refresh_from_db()
        self.assertEqual(note.subjective, "New")
        self.assertIsNone(note.signed_at)

    def test_signing_confirmation_and_nonmutating_get(self):
        note = self.note()
        url = self.url("note_sign", note.encounter, note.pk)
        self.assertContains(self.client.get(url), "Confirm and sign note")
        self.assertIsNone(Note.objects.get(pk=note.pk).signed_at)
        self.assertEqual(self.client.post(url, {"version": 1}).status_code, 400)
        self.assertEqual(self.client.post(url, {"version": 1, "confirmed": True}).status_code, 302)
        note.refresh_from_db()
        self.assertIsNotNone(note.signed_at)
        self.assertEqual(note.author, self.physician)
        self.assertTrue(note.clinicalevent_set.filter(audit__action="note_sign").exists())

    def test_signed_note_immutable_in_view_service_and_model_save(self):
        note = self.note()
        sign_note(self.physician, note.pk, 1, True)
        before = Note.objects.values().get(pk=note.pk)
        self.assertEqual(self.client.post(self.url("note_edit", note.encounter), self.data(version=2)).status_code, 409)
        with self.assertRaises(ClinicalConflict):
            save_note(self.physician, note.encounter_id, self.data(), 2)
        with self.assertRaises(ClinicalConflict):
            sign_note(self.physician, note.pk, 2, True)
        note.subjective = "Attempted overwrite"
        with self.assertRaises(ValidationError):
            note.save()
        self.assertEqual(Note.objects.values().get(pk=note.pk), before)

    def test_completion_rules_and_timestamps(self):
        encounter = self.start()
        with self.assertRaises(ValidationError):
            complete_encounter(self.physician, encounter.pk, 1)
        note = self.note(encounter)
        with self.assertRaises(ValidationError):
            complete_encounter(self.physician, encounter.pk, 1)
        sign_note(self.physician, note.pk, 1, True)
        with self.assertRaises(ClinicalConflict):
            complete_encounter(self.physician, encounter.pk, 2)
        complete_encounter(self.physician, encounter.pk, 1)
        encounter.refresh_from_db()
        self.assertEqual(encounter.status, "completed")
        self.assertGreaterEqual(encounter.completed_at, encounter.started_at)
        with self.assertRaises(ClinicalConflict):
            complete_encounter(self.physician, encounter.pk, 2)
        with self.assertRaises(ClinicalConflict):
            save_note(self.physician, encounter.pk, self.data(), 2)

    def test_patient_encounter_and_note_url_isolation(self):
        encounter = self.start()
        note = self.note(encounter)
        self.client.force_login(self.users["Administrator"])
        for name, extra in [("encounter_detail", []), ("note_edit", []), ("note_sign", [note.pk]), ("encounter_complete", [])]:
            url = reverse(name, args=[self.unrelated.pk, encounter.pk, *extra])
            response = self.client.post(url, self.data(version=1, confirmed=True))
            self.assertIn(response.status_code, [404, 405])
        self.client.force_login(self.physician)
        self.assertEqual(self.client.get(self.url("note_sign", encounter, note.pk + 999)).status_code, 404)

    def test_forged_patient_and_author_ignored(self):
        encounter = self.start()
        self.client.post(self.url("note_edit", encounter), self.data(version=0, patient=self.unrelated.pk, author=self.other.pk))
        note = Note.objects.get(encounter=encounter)
        self.assertEqual(note.patient, self.patient)
        self.assertEqual(note.author, self.physician)

    def test_audit_failure_rolls_back_clinical_changes(self):
        with patch("careflow.clinical.services._event", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.start()
        self.assertFalse(Encounter.objects.exists())
        encounter = self.start()
        with patch("careflow.clinical.services._event", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.note(encounter)
        self.assertFalse(Note.objects.exists())

    def test_appointment_cancel_after_start_denied_provenance_retained(self):
        self.start()
        with self.assertRaises(AppointmentConflict):
            transition_appointment(self.users["FrontDesk"], self.appointment.pk, "cancel", 1, "Synthetic")
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "arrived")
        self.assertEqual(self.appointment.checked_in_by, self.users["FrontDesk"])
        self.assertFalse(AppointmentEvent.objects.exists())

    def test_anonymous_and_inactive_access(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("physician_workspace")).status_code, 302)
        self.physician.is_active = False
        self.physician.save()
        with self.assertRaises(PermissionDenied):
            self.start()

    def test_csrf_protects_clinical_posts(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.physician)
        self.assertEqual(client.post(reverse("encounter_start", args=[self.appointment.pk]), {"version": 1}).status_code, 403)
        self.assertFalse(Encounter.objects.exists())

    def test_clinical_pages_banner_and_escaping(self):
        note = self.note()
        note.subjective = "<script>alert('synthetic')</script>"
        note.save()
        response = self.client.get(self.url("encounter_detail", note.encounter))
        self.assertContains(response, "DEMO — NOT FOR CLINICAL USE")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert")

    def test_multi_role_admin_has_no_other_physician_signing_right(self):
        note = self.note()
        admin = self.users["Administrator"]
        admin.groups.add(Group.objects.get(name="Physician"))
        with self.assertRaises(PermissionDenied):
            sign_note(admin, note.pk, 1, True)

    def test_encounter_context_validation(self):
        encounter = Encounter(appointment=self.appointment, patient=self.unrelated, physician=self.physician)
        with self.assertRaises(ValidationError):
            encounter.full_clean()

    def test_note_author_context_validation(self):
        encounter = self.start()
        with self.assertRaises(ValidationError):
            Note(encounter=encounter, author=self.other).full_clean()


class ConcurrentEncounterTests(TransactionTestCase):
    def test_parallel_start_has_one_encounter_and_one_audit_event(self):
        physician = get_user_model().objects.create_user(username="parallel-physician")
        physician.groups.add(Group.objects.get_or_create(name="Physician")[0])
        patient = Patient.objects.create(mrn="PARALLEL-DEMO", first_name="Synthetic", last_name="Parallel",
                                         dob=date(1980, 1, 1), sex="unknown")
        now = timezone.now()
        appointment = Appointment.objects.create(patient=patient, physician=physician,
            start_at=now, end_at=now + timedelta(minutes=30), status="arrived", appointment_type="Synthetic")
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=physician.pk)
                barrier.wait(timeout=10)
                try:
                    start_encounter(actor, appointment.pk, 1)
                    return "started"
                except ClinicalConflict:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(results, ["started", "conflict"])
        self.assertEqual(Encounter.objects.count(), 1)
        self.assertEqual(ClinicalEvent.objects.count(), 1)
