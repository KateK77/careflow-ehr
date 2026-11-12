"""Regression checks for state and provenance across module boundaries."""
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Encounter, Note
from careflow.history.models import HistoryEvent, MedicalHistory
from careflow.hospital.models import AdmissionRequest, HospitalEvent
from careflow.hospital.test_emergency import EDFixture
from careflow.imaging.test_workflow import WorkflowFixture
from careflow.imaging.workflow import current_report
from careflow.labs.models import LabOrder
from careflow.mar.tests import MARFixture
from careflow.nursing.integration_support import IntegrationFixture
from careflow.nursing.models import NursingEvent, VitalObservation
from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientVisibleResultRelease
from careflow.portal.records import release_result
from careflow.portal.tests import PortalFixture
from careflow.scheduling.models import Appointment


class OutpatientHandoffTests(IntegrationFixture, TestCase):
    def setUp(self):
        self.make_staff()
        self.client.force_login(self.staff["FrontDesk"])
        self.registration = {
            "mrn": "SYN-HANDOFF", "first_name": "Synthetic", "last_name": "Handoff",
            "dob": "1980-01-01", "sex": "unknown", "version": 1, "synthetic_only": True,
        }

    def register(self):
        response = self.client.post(reverse("patient_create"), self.registration)
        self.assertEqual(response.status_code, 302)
        return Patient.objects.get(mrn=self.registration["mrn"])

    def appointment(self, patient, status="arrived"):
        now = timezone.now()
        return Appointment.objects.create(patient=patient, physician=self.staff["Physician"], status=status,
                                          start_at=now, end_at=now + timedelta(minutes=30),
                                          appointment_type="Synthetic handoff")

    def test_registration_retains_actor_in_patient_audit(self):
        patient = self.register()
        event = AuditEvent.objects.get(patient=patient, action="patient_create")
        self.assertEqual(event.actor, self.staff["FrontDesk"])
        self.assertIn("mrn", event.changed_fields)

    def test_invalid_contact_does_not_create_registration_or_success_audit(self):
        response = self.client.post(reverse("patient_create"), {**self.registration, "email": "bad@@synthetic"})
        self.assertFormError(response.context["form"], "email", "Enter a valid email address.")
        self.assertFalse(Patient.objects.exists())
        self.assertFalse(AuditEvent.objects.filter(action="patient_create").exists())

    def test_booking_review_token_cannot_change_patient_on_confirmation(self):
        patient = self.register()
        other = Patient.objects.create(mrn="SYN-HANDOFF-B", first_name="Other", last_name="Synthetic",
                                       dob=patient.dob, sex="unknown")
        start = timezone.localtime(timezone.now() + timedelta(days=2)).replace(hour=10)
        form = {"patient": patient.pk, "physician": self.staff["Physician"].pk,
                "start_at": start.isoformat(), "duration": 30, "appointment_type": "Synthetic visit", "version": 1}
        url = reverse("appointment_create")
        review = self.client.post(url, {**form, "action": "review"})
        token = review.context["review_token"]
        response = self.client.post(url, {**form, "patient": other.pk, "action": "confirm", "review_token": token})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Appointment.objects.exists())

    def test_invalid_unit_does_not_persist_vitals_or_nursing_audit(self):
        appointment = self.appointment(self.register())
        self.client.force_login(self.staff["Nurse"])
        url = reverse("nursing_create", args=[appointment.patient_id, appointment.pk, "vitals"])
        response = self.client.post(url, self.vital_payload(temperature="98.6", temperature_unit="C"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("temperature", response.context["form"].errors)
        self.assertFalse(VitalObservation.objects.exists())
        self.assertFalse(NursingEvent.objects.exists())

    def test_vital_panel_provenance_stays_on_appointment_when_encounter_starts(self):
        appointment = self.appointment(self.register())
        self.client.force_login(self.staff["Nurse"])
        url = reverse("nursing_create", args=[appointment.patient_id, appointment.pk, "vitals"])
        self.assertEqual(self.client.post(url, self.vital_payload()).status_code, 302)
        self.client.force_login(self.staff["Physician"])
        self.assertEqual(self.client.post(reverse("encounter_start", args=[appointment.pk]),
                                          {"version": appointment.version}).status_code, 302)
        panel = VitalObservation.objects.get()
        self.assertIsNone(panel.encounter_id)
        self.assertEqual(panel.appointment_id, Encounter.objects.get().appointment_id)
        self.assertEqual(NursingEvent.objects.get(observation=panel).audit.actor, self.staff["Nurse"])

    def test_history_audit_links_to_patient_and_chart_after_encounter_start(self):
        patient = self.register()
        appointment = self.appointment(patient)
        self.client.force_login(self.staff["Physician"])
        self.assertEqual(self.client.post(reverse("encounter_start", args=[appointment.pk]),
                                          {"version": appointment.version}).status_code, 302)
        response = self.client.post(reverse("history_create", args=[patient.pk, "medical"]),
                                    self.history_payload("Synthetic prior history", category="medical"))
        self.assertEqual(response.status_code, 302)
        history = MedicalHistory.objects.get(patient=patient)
        event = HistoryEvent.objects.get(patient=patient, record_id=history.pk)
        self.assertEqual(event.audit.actor, self.staff["Physician"])
        self.assertIsNone(event.encounter_id)
        self.assertContains(self.client.get(reverse("patient_chart", args=[patient.pk])), response.url)

    def test_cancellation_after_checkin_keeps_original_checkin_provenance(self):
        appointment = self.appointment(self.register(), status="scheduled")
        url = reverse("appointment_transition", args=[appointment.pk])
        self.assertEqual(self.client.post(url, {"action": "arrive", "version": 1}).status_code, 302)
        appointment.refresh_from_db()
        provenance = (appointment.checked_in_at, appointment.checked_in_by_id)
        self.assertEqual(self.client.post(url, {"action": "cancel", "version": appointment.version,
                                                "reason": "Synthetic cancellation"}).status_code, 302)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, "cancelled")
        self.assertEqual((appointment.checked_in_at, appointment.checked_in_by_id), provenance)
        self.assertFalse(Encounter.objects.filter(appointment=appointment).exists())

    def test_wrong_patient_note_url_cannot_create_soap(self):
        patient = self.register()
        appointment = self.appointment(patient)
        self.client.force_login(self.staff["Physician"])
        self.assertEqual(self.client.post(reverse("encounter_start", args=[appointment.pk]),
                                          {"version": appointment.version}).status_code, 302)
        visit = Encounter.objects.get()
        wrong = reverse("note_edit", args=[patient.pk + 100, visit.pk])
        self.assertEqual(self.client.post(wrong, self.soap_payload()).status_code, 404)
        self.assertFalse(Note.objects.exists())


class ResultHandoffTests(PortalFixture, TestCase):
    def setUp(self):
        self.setup_portal()

    def test_release_event_names_patient_and_ordering_actor(self):
        release = self.release()
        self.assertEqual(release.audit.patient, self.patient)
        self.assertEqual(release.audit.actor, self.physician)
        self.assertEqual(release.audit.action, "portal_result_release")

    def test_corrected_release_keeps_prior_release_provenance(self):
        prior = self.release()
        revised = self.correct()
        release_result(self.physician, revised.pk, self.physician.pk)
        prior.refresh_from_db()
        self.assertEqual(prior.result_id, self.original.pk)
        self.assertEqual(PatientVisibleResultRelease.objects.filter(audit__patient=self.patient).count(), 2)

    def test_order_patient_mismatch_fails_closed_for_already_released_result(self):
        self.release()
        LabOrder.objects.filter(pk=self.order.pk).update(patient=self.foreign)
        for actor in (self.portal_a, self.portal_b):
            self.client.force_login(actor)
            self.assertEqual(self.client.get(reverse("portal_result", args=[self.original.pk])).status_code, 404)


class PharmacyHandoffTests(MARFixture, TestCase):
    def test_wrong_patient_cannot_record_against_valid_dispense(self):
        from careflow.mar.models import MedicationAdministrationEvent
        from careflow.mar.services import record

        self.setup_pharmacy()
        receipt = self.dispense_order()
        with self.assertRaises(PermissionDenied):
            record(self.staff["Nurse"], receipt.pk, self.foreign.pk, self.encounter.pk, version=0,
                   key=uuid.uuid4(), confirmed=True, occurred_at=timezone.now(), quantity=receipt.quantity)
        self.assertFalse(MedicationAdministrationEvent.objects.filter(receipt=receipt).exists())


class ImagingHandoffTests(WorkflowFixture, TestCase):
    def test_withdrawal_notice_preserves_reviewed_revision_and_has_no_findings(self):
        self.setup_workflow()
        report = self.report_final()
        self.review(report)
        self.command("imaging_withdraw", reason="Synthetic context mismatch", withdrawal_kind="context_error")
        notice = current_report(self.order)
        self.assertEqual((notice.status, notice.findings, notice.impression), ("withdrawn", "", ""))
        self.assertEqual(notice.based_on_id, report.pk)
        report.refresh_from_db()
        self.assertEqual(report.review.physician, self.physician)


class EmergencyHandoffTests(EDFixture, TestCase):
    def setUp(self):
        self.setup_ed()

    def test_pending_inpatient_request_blocks_parallel_ed_registration(self):
        pending = self.admission_request()
        with self.assertRaises(ValidationError):
            self.arrival()
        pending.refresh_from_db()
        self.assertEqual(pending.status, "pending")
        self.assertFalse(HospitalEvent.objects.filter(audit__action="ed_register").exists())

    def test_ed_admission_links_bed_and_ed_audits_to_same_patient(self):
        visit = self.provider_visit()
        admitted = self.advance(visit, "ed_admit", bed_id=self.bed.pk, note="Synthetic admission")
        stay = admitted.inpatient_stay
        bed_event = stay.events.get(audit__action="hospital_admit")
        ed_event = admitted.events.get(audit__action="ed_admit")
        self.assertEqual(bed_event.next_bed, self.bed)
        self.assertEqual(bed_event.audit.patient_id, ed_event.audit.patient_id)
        self.assertEqual(ed_event.details["after"], "admitted")
        self.assertEqual(AdmissionRequest.objects.get(pk=stay.request_id).status, "admitted")
