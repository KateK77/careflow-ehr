import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Note
from careflow.medications.models import PharmacyDispenseEvent
from careflow.medications.services import MedicationConflict, snapshot
from careflow.medications.test_pharmacy import PharmacyFixture
from .access import receipts_for
from .models import MedicationAdministrationEvent
from .services import record


class MARFixture(PharmacyFixture):
    def dispense_order(self):
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("approve", 1)
        self.pharmacy_action("dispense", 2, quantity=self.signed.quantity)
        return PharmacyDispenseEvent.objects.get(review__order=self.signed)

    def record_event(self, receipt, actor=None, **changes):
        data = {"version": 0, "key": uuid.uuid4(), "confirmed": True,
                "quantity": receipt.quantity, "occurred_at": timezone.now()}
        data.update(changes)
        return record(actor or self.staff["Nurse"], receipt.pk, self.patient.pk, self.encounter.pk, **data)


class MARTests(MARFixture, TestCase):
    def setUp(self):
        self.setup_pharmacy()

    def test_requires_approved_dispense_and_does_not_auto_record(self):
        nurse = self.staff["Nurse"]
        self.assertFalse(receipts_for(nurse).exists())
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("approve", 1)
        self.assertFalse(receipts_for(nurse).exists())
        self.pharmacy_action("dispense", 2, quantity=self.signed.quantity)
        self.assertEqual(receipts_for(nurse).count(), 1)
        self.assertFalse(MedicationAdministrationEvent.objects.exists())

    def test_record_idempotency_version_and_signed_order_preservation(self):
        receipt = self.dispense_order()
        before = snapshot(self.signed)
        payload = {"key": uuid.uuid4(), "occurred_at": timezone.now()}
        first = self.record_event(receipt, **payload)
        self.assertEqual(self.record_event(receipt, **payload), first)
        with self.assertRaises(MedicationConflict):
            self.record_event(receipt, **payload, notes="Different payload")
        with self.assertRaises(MedicationConflict):
            self.record_event(receipt)
        with self.assertRaises(MedicationConflict):
            self.record_event(receipt, version=1)
        self.assertEqual(receipt.administration_events.count(), 1)
        self.assertEqual(first.actor, self.staff["Nurse"])
        self.assertEqual(first.audit.patient, self.patient)
        self.signed.refresh_from_db()
        self.assertEqual(snapshot(self.signed), before)
        self.assertEqual(receipt.review.status, "approved")

    def test_wrong_context_and_invalid_fields(self):
        receipt = self.dispense_order()
        for patient_id, encounter_id in ((self.foreign.pk, self.encounter.pk), (self.patient.pk, 99999)):
            with self.assertRaises(PermissionDenied):
                record(self.staff["Nurse"], receipt.pk, patient_id, encounter_id, version=0,
                       key=uuid.uuid4(), confirmed=True, quantity=receipt.quantity, occurred_at=timezone.now())
        for changes in ({"confirmed": False}, {"quantity": 0}, {"occurred_at": timezone.now() + timedelta(hours=1)},
                        {"occurred_at": self.encounter.started_at - timedelta(seconds=1)}):
            with self.assertRaises(ValidationError):
                self.record_event(receipt, **changes)
        self.assertFalse(receipt.administration_events.exists())

    def test_roles_and_csrf(self):
        receipt = self.dispense_order()
        url = reverse("mar_administer", args=[self.patient.pk, self.encounter.pk, receipt.pk])
        detail = reverse("mar_detail", args=[receipt.pk])
        for actor in (self.admin, self.physician, self.other, self.staff["FrontDesk"], self.staff["Lab Staff"], self.pharmacist):
            self.client.force_login(actor)
            self.assertEqual(self.client.get(url).status_code, 403)
            with self.assertRaises(PermissionDenied):
                self.record_event(receipt, actor=actor)
            response = self.client.get(detail)
            if actor in (self.admin, self.physician):
                self.assertContains(response, "Effective MAR state")
                self.assertNotContains(response, "Record simulated administration")
            else:
                self.assertIn(response.status_code, {403, 404})
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.staff["Nurse"])
        self.assertEqual(protected.post(url, {}).status_code, 403)

    def test_audit_rollback(self):
        receipt = self.dispense_order()
        with patch("careflow.mar.services.AuditEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.record_event(receipt)
        self.assertFalse(receipt.administration_events.exists())

    def test_completion_blocks_recording_and_preserves_soap(self):
        self.finish_encounter()
        before = Note.objects.values().get(encounter=self.encounter)
        receipt = self.dispense_order()
        with self.assertRaises(MedicationConflict):
            self.record_event(receipt)
        self.assertEqual(Note.objects.values().get(encounter=self.encounter), before)
        self.assertFalse(receipts_for(self.staff["Nurse"]).exists())

    def test_worklist_filters_effective_status_and_context(self):
        receipt = self.dispense_order()
        self.client.force_login(self.staff["Nurse"])
        url = reverse("mar_worklist")
        filters = {"patient": self.patient.pk, "encounter": self.encounter.pk,
                   "medication": "amber", "status": "pending"}
        self.assertContains(self.client.get(url, filters), "Synthetic Amber")
        self.assertNotContains(self.client.get(url, {**filters, "patient": self.foreign.pk}), "Synthetic Amber")
        self.record_event(receipt)
        self.assertNotContains(self.client.get(url, filters), "Synthetic Amber")
        self.assertContains(self.client.get(url, {**filters, "status": "administered"}), "Synthetic Amber")
