import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Note
from careflow.medications.services import MedicationConflict, snapshot
from careflow.patients.models import AuditEvent
from .models import MedicationAdministrationEvent
from .tests import MARFixture


class MARExceptionTests(MARFixture, TestCase):
    def setUp(self):
        self.setup_pharmacy()
        self.receipt = self.dispense_order()

    def exception(self, status="held", **changes):
        return self.record_event(self.receipt, **{
            "status": status, "quantity": None, "reason": "Fictional exception", **changes,
        })

    def test_exception_reasons_and_quantity_are_required_by_state(self):
        for status in ("held", "refused", "omitted"):
            for invalid in ({"reason": "   "}, {"quantity": self.receipt.quantity}):
                with self.subTest(status=status, invalid=invalid), self.assertRaises(ValidationError):
                    self.exception(status, **invalid)
        self.assertFalse(self.receipt.administration_events.exists())

    def test_held_can_resolve_and_refused_is_terminal(self):
        first = self.exception()
        with self.assertRaises(MedicationConflict):
            self.exception(version=1)
        refused = self.exception("refused", version=1)
        self.assertEqual((refused.status, refused.revision, refused.quantity), ("refused", 2, None))
        with self.assertRaises(MedicationConflict):
            self.record_event(self.receipt, version=2)
        first.refresh_from_db()
        self.assertEqual(first.status, "held")

    def test_held_to_administered_rejects_earlier_resolution_time(self):
        from datetime import timedelta
        held = self.exception()
        with self.assertRaises(ValidationError):
            self.record_event(self.receipt, version=1, occurred_at=held.occurred_at - timedelta(microseconds=1))
        result = self.record_event(self.receipt, version=1)
        self.assertEqual((result.status, result.revision), ("administered", 2))

    def test_correction_preserves_history_replays_and_rejects_stale(self):
        original = self.record_event(self.receipt)
        before = snapshot(original)
        correction = {
            "version": 1, "correction": True, "correction_reason": "Entered on wrong outcome",
            "key": uuid.uuid4(), "occurred_at": original.occurred_at,
        }
        amended = self.exception("omitted", **correction)
        self.assertEqual(self.exception("omitted", **correction), amended)
        with self.assertRaises(MedicationConflict):
            self.exception("refused", **{**correction, "key": uuid.uuid4()})
        original.refresh_from_db()
        self.assertEqual(snapshot(original), before)
        self.assertEqual(amended.audit.action, "mar_correct")
        with self.assertRaises(ValidationError):
            original.save()
        with self.assertRaises(ValidationError):
            original.delete()

    def test_requires_prior_event_and_explicit_correction_reason(self):
        with self.assertRaises(MedicationConflict):
            self.exception("omitted", correction=True, correction_reason="No original event")
        self.exception()
        with self.assertRaises(ValidationError):
            self.exception("omitted", version=1, correction=True)

    def test_completed_encounter_cannot_be_corrected_and_soap_unchanged(self):
        order_before = snapshot(self.signed)
        self.record_event(self.receipt)
        self.finish_encounter()
        note_before = Note.objects.values().get(encounter=self.encounter)
        with self.assertRaises(MedicationConflict):
            self.exception("omitted", version=1, correction=True, correction_reason="Too late")
        self.assertEqual(Note.objects.values().get(encounter=self.encounter), note_before)
        self.signed.refresh_from_db()
        self.assertEqual(snapshot(self.signed), order_before)
        self.client.force_login(self.staff["Nurse"])
        response = self.client.get(reverse("mar_detail", args=[self.receipt.pk]))
        self.assertContains(response, "Version 1")
        self.assertNotContains(response, "Correct MAR documentation")

    def test_audit_rolls_back_when_correction_event_write_fails(self):
        self.record_event(self.receipt)
        with patch("careflow.mar.services.MedicationAdministrationEvent.objects.create", side_effect=RuntimeError("unavailable")):
            with self.assertRaises(RuntimeError):
                self.exception("omitted", version=1, correction=True, correction_reason="Failed write")
        self.assertEqual(self.receipt.administration_events.count(), 1)
        self.assertFalse(AuditEvent.objects.filter(patient=self.patient, action="mar_correct").exists())

    def test_physician_integration_shows_effective_state_with_read_only_history(self):
        self.exception("refused")
        self.exception("omitted", version=1, correction=True, correction_reason="Wrong exception")
        self.client.force_login(self.physician)
        for route, args in (
            ("physician_workspace", []),
            ("nursing_workspace", []),
            ("patient_chart", [self.patient.pk]),
            ("encounter_detail", [self.patient.pk, self.encounter.pk]),
            ("med_detail", [self.signed.public_id]),
            ("med_encounter_history", [self.patient.pk, self.encounter.pk]),
        ):
            response = self.client.get(reverse(route, args=args))
            self.assertContains(response, "Omitted / Not given")
            self.assertContains(response, reverse("mar_detail", args=[self.receipt.pk]))
        detail = self.client.get(reverse("mar_detail", args=[self.receipt.pk]))
        self.assertContains(detail, "Superseded record")
        self.assertContains(detail, "Wrong exception")
        self.assertNotContains(detail, "Correct MAR documentation")
        with self.assertRaises(PermissionDenied):
            self.exception("refused", version=2, correction=True, correction_reason="Wrong actor", actor=self.physician)


class MARConcurrencyTests(MARFixture, TransactionTestCase):
    def test_competing_submissions_create_one_initial_outcome(self):
        self.setup_pharmacy()
        receipt = self.dispense_order()
        nurse_id = self.staff["Nurse"].pk
        barrier = Barrier(2)

        def attempt(_):
            close_old_connections()
            try:
                nurse = get_user_model().objects.get(pk=nurse_id)
                barrier.wait(timeout=10)
                self.record_event(receipt, actor=nurse)
                return True
            except MedicationConflict:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(MedicationAdministrationEvent.objects.filter(receipt=receipt).count(), 1)
