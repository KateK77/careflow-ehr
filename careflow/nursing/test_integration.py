from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Encounter, Note
from careflow.history.models import AllergyState, EncounterDiagnosis, MedicalHistory, MedicationStatement, Problem
from careflow.patients.models import AuditEvent, Patient
from careflow.scheduling.models import Appointment
from .integration_support import IntegrationFixture, TEST_CLINIC_ZONE
from .models import NursingEvent, RoomingAssessment, VitalObservation


@override_settings(TIME_ZONE=TEST_CLINIC_ZONE)
class CrossPhaseIntegrationTests(IntegrationFixture, TestCase):
    def setUp(self):
        self.make_staff()
        self.client.force_login(self.staff["FrontDesk"])
        response = self.client.post(reverse("patient_create"), {
            "mrn": "INTEGRATION-001", "first_name": "Synthetic", "last_name": "Integration",
            "dob": "1985-01-01", "sex": "unknown", "version": 1, "synthetic_only": True,
        })
        self.assertEqual(response.status_code, 302)
        self.patient = Patient.objects.get(mrn="INTEGRATION-001")
        self.appointment = self.book(self.staff["Physician"])

    def book(self, physician, offset=1):
        self.client.force_login(self.staff["FrontDesk"])
        start = timezone.localtime(timezone.now() + timedelta(hours=offset)).replace(second=0, microsecond=0)
        payload = {"patient": self.patient.pk, "physician": physician.pk, "start_at": start.strftime("%Y-%m-%dT%H:%M"),
                   "duration": 30, "appointment_type": "Synthetic integrated visit", "reason": "Fictional workflow",
                   "version": 1, "action": "review"}
        review = self.client.post(reverse("appointment_create"), payload)
        self.assertEqual(review.status_code, 200)
        self.assertFalse(Appointment.objects.filter(patient=self.patient, physician=physician, start_at=start).exists())
        confirm = self.client.post(reverse("appointment_create"), {
            **payload, "action": "confirm", "review_token": review.context["review_token"],
        })
        self.assertEqual(confirm.status_code, 302)
        return Appointment.objects.latest("pk")

    def arrive_and_room(self):
        self.client.force_login(self.staff["FrontDesk"])
        response = self.client.post(reverse("appointment_transition", args=[self.appointment.pk]),
                                    {"action": "arrive", "version": self.appointment.version})
        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertFalse(Encounter.objects.exists())
        self.client.force_login(self.staff["Nurse"])
        for kind, payload in [("assessment", self.assessment_payload()), ("vitals", self.vital_payload())]:
            response = self.client.post(reverse("nursing_create", args=[self.patient.pk, self.appointment.pk, kind]), payload)
            self.assertEqual(response.status_code, 302)
        self.assertFalse(Encounter.objects.exists())
        self.assertIsNone(RoomingAssessment.objects.get().encounter_id)
        self.assertIsNone(VitalObservation.objects.get().encounter_id)
        self.assertEqual(self.client.post(reverse("encounter_start", args=[self.appointment.pk]), {"version": self.appointment.version}).status_code, 403)

    def start(self, appointment=None, physician=None):
        appointment = appointment or self.appointment
        self.client.force_login(physician or self.staff["Physician"])
        response = self.client.post(reverse("encounter_start", args=[appointment.pk]), {"version": appointment.version})
        self.assertEqual(response.status_code, 302)
        return Encounter.objects.get(appointment=appointment)

    def review_history(self, encounter):
        for kind, payload in [
            ("medical", self.history_payload("Synthetic prior history", category="medical")),
            ("problems", self.history_payload("Synthetic longitudinal problem", status="active", code="MOCK-I")),
            ("allergies", self.history_payload("Synthetic allergen", reaction="Fictional reaction", severity="mild", status="active", verification="confirmed")),
            ("medications", self.history_payload("Synthetic medication statement", dose="Mock dose description", route="Mock route", frequency="Mock frequency", status="active")),
        ]:
            response = self.client.post(reverse("history_create", args=[self.patient.pk, kind]), payload)
            self.assertEqual(response.status_code, 302)
            record_id = int(response.url.rstrip("/").split("/")[-1])
            review = self.client.post(reverse("history_review", args=[self.patient.pk, kind, record_id]),
                                      {"version": 1, "synthetic_confirmed": True})
            self.assertEqual(review.status_code, 302)
        problem = Problem.objects.get()
        response = self.client.post(reverse("diagnosis_create", args=[self.patient.pk, encounter.pk]),
            self.history_payload("Synthetic primary diagnosis", rank="primary", code="MOCK-DX", problem=problem.pk))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(EncounterDiagnosis.objects.get().patient, self.patient)
        self.assertEqual(EncounterDiagnosis.objects.get().problem, problem)
        self.assertEqual(AllergyState.objects.get().status, "documented")
        for model in [MedicalHistory, Problem, MedicationStatement]:
            self.assertEqual(model.objects.get().reviewed_by, self.staff["Physician"])

    def sign(self, encounter):
        args = [self.patient.pk, encounter.pk]
        self.assertEqual(self.client.post(reverse("note_edit", args=args), self.soap_payload(plan="")).status_code, 302)
        note = Note.objects.get(encounter=encounter)
        sign_url = reverse("note_sign", args=[*args, note.pk])
        self.assertEqual(self.client.post(sign_url, {"version": 1, "confirmed": True}).status_code, 400)
        self.assertEqual(self.client.post(reverse("note_edit", args=args), self.soap_payload(version=1)).status_code, 302)
        self.assertContains(self.client.get(reverse("note_edit", args=args)), "Fictional plan only")
        self.assertEqual(self.client.post(sign_url, {"version": 2, "confirmed": True}).status_code, 302)
        note.refresh_from_db()
        self.assertIsNotNone(note.signed_at)
        self.assertEqual(note.author, self.staff["Physician"])
        return note

    def test_complete_outpatient_lifecycle_preserves_provenance_and_signed_note(self):
        self.arrive_and_room()
        checkin = (self.appointment.checked_in_at, self.appointment.checked_in_by_id, self.appointment.version)
        encounter = self.start()
        detail = self.client.get(reverse("encounter_detail", args=[self.patient.pk, encounter.pk]))
        self.assertContains(detail, "Synthetic integration complaint")
        self.assertContains(detail, "37.20 °C")
        self.review_history(encounter)
        note = self.sign(encounter)
        signed = Note.objects.values().get(pk=note.pk)
        self.client.force_login(self.staff["Nurse"])
        vital = VitalObservation.objects.get()
        self.assertEqual(self.client.post(reverse("nursing_edit", args=[self.patient.pk, self.appointment.pk, "vitals", vital.pk]),
                                         self.vital_payload(version=1, heart_rate=71)).status_code, 302)
        self.assertEqual(Note.objects.values().get(pk=note.pk), signed)
        correction = NursingEvent.objects.filter(observation=vital).first()
        self.assertEqual(correction.audit.actor, self.staff["Nurse"])
        self.assertEqual(correction.before["heart_rate"], 70)
        self.assertEqual(correction.after["heart_rate"], 71)
        self.client.force_login(self.staff["Physician"])
        self.assertEqual(self.client.post(reverse("encounter_complete", args=[self.patient.pk, encounter.pk]), {"version": 1}).status_code, 302)
        encounter.refresh_from_db()
        self.appointment.refresh_from_db()
        self.assertEqual(encounter.status, "completed")
        self.assertEqual(self.appointment.status, "arrived")
        self.assertEqual((self.appointment.checked_in_at, self.appointment.checked_in_by_id, self.appointment.version), checkin)
        self.assertEqual(self.client.post(reverse("note_edit", args=[self.patient.pk, encounter.pk]), self.soap_payload(version=3)).status_code, 409)
        self.assertEqual(self.client.post(reverse("diagnosis_create", args=[self.patient.pk, encounter.pk]), self.history_payload("Denied diagnosis", rank="secondary")).status_code, 403)
        self.assertEqual(self.client.post(reverse("history_create", args=[self.patient.pk, "medical"]), self.history_payload("Denied history", category="medical")).status_code, 403)
        self.client.force_login(self.staff["Nurse"])
        self.assertEqual(self.client.post(reverse("nursing_create", args=[self.patient.pk, self.appointment.pk, "vitals"]), self.vital_payload()).status_code, 403)
        self.assertEqual(Note.objects.values().get(pk=note.pk), signed)
        self.client.force_login(self.staff["Physician"])
        chart = self.client.get(reverse("patient_chart", args=[self.patient.pk]))
        for label in ["nursing_vitals_edit", "history_medical_review", "note_sign", "encounter_complete"]:
            self.assertContains(chart, label)
        actions = set(AuditEvent.objects.filter(patient=self.patient).values_list("action", flat=True))
        self.assertTrue({"patient_create", "appointment_create", "appointment_arrive", "nursing_assessment_create",
                         "nursing_vitals_create", "encounter_start", "history_medical_review", "note_sign", "encounter_complete"} <= actions)

    def test_cancellation_after_rooming_retains_nursing_data_without_encounter(self):
        self.arrive_and_room()
        saved = VitalObservation.objects.values().get()
        self.client.force_login(self.staff["FrontDesk"])
        response = self.client.post(reverse("appointment_transition", args=[self.appointment.pk]),
            {"action": "cancel", "version": self.appointment.version, "reason": "Synthetic cancellation after rooming"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Encounter.objects.exists())
        self.assertEqual(VitalObservation.objects.values().get(), saved)
        self.client.force_login(self.staff["Nurse"])
        self.assertEqual(self.client.post(reverse("nursing_edit", args=[self.patient.pk, self.appointment.pk, "vitals", saved["id"]]), self.vital_payload(version=1)).status_code, 403)
        self.assertContains(self.client.get(reverse("nursing_flowsheet", args=[self.patient.pk])), "37.20 °C")
        self.client.force_login(self.staff["Physician"])
        self.assertEqual(self.client.post(reverse("encounter_start", args=[self.appointment.pk]), {"version": self.appointment.version + 1}).status_code, 409)

    def test_shared_patient_history_does_not_expand_encounter_or_nursing_scope(self):
        self.arrive_and_room()
        encounter = self.start()
        self.review_history(encounter)
        other = get_user_model().objects.create_user(username="integration-other-physician")
        other.groups.add(Group.objects.get(name="Physician"))
        self.book(other, offset=2)
        self.client.force_login(other)
        chart = self.client.get(reverse("patient_chart", args=[self.patient.pk]))
        self.assertContains(chart, "Medical history: 1 records")
        self.assertNotContains(chart, "Synthetic integration complaint")
        self.assertNotContains(chart, "history_diagnoses_create")
        self.assertEqual(self.client.get(reverse("encounter_detail", args=[self.patient.pk, encounter.pk])).status_code, 404)
        vital = VitalObservation.objects.get()
        self.assertEqual(self.client.get(reverse("nursing_record", args=[self.patient.pk, self.appointment.pk, "vitals", vital.pk])).status_code, 404)
        for role in ["Nurse", "Administrator", "FrontDesk"]:
            self.client.force_login(self.staff[role])
            self.assertEqual(self.client.post(reverse("diagnosis_create", args=[self.patient.pk, encounter.pk]), self.history_payload("Denied", rank="secondary")).status_code, 403)
            self.assertEqual(self.client.post(reverse("note_edit", args=[self.patient.pk, encounter.pk]), self.soap_payload()).status_code, 403)
            self.assertEqual(self.client.post(reverse("history_create", args=[self.patient.pk, "medical"]), self.history_payload("Denied", category="medical")).status_code, 403)

    def test_new_treatment_assignment_preserves_history_write_without_reopening_completed_context(self):
        self.arrive_and_room()
        encounter = self.start()
        self.sign(encounter)
        self.assertEqual(self.client.post(reverse("encounter_complete", args=[self.patient.pk, encounter.pk]), {"version": 1}).status_code, 302)
        self.book(self.staff["Physician"], offset=3)
        self.client.force_login(self.staff["Physician"])
        self.assertEqual(self.client.post(reverse("history_create", args=[self.patient.pk, "medical"]), self.history_payload("Synthetic ongoing care", category="medical")).status_code, 302)
        self.assertEqual(self.client.post(reverse("diagnosis_create", args=[self.patient.pk, encounter.pk]), self.history_payload("Denied", rank="secondary")).status_code, 403)
        self.client.force_login(self.staff["Nurse"])
        self.assertEqual(self.client.post(reverse("nursing_create", args=[self.patient.pk, self.appointment.pk, "vitals"]), self.vital_payload()).status_code, 403)
