import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from careflow.clinical.models import Note
from careflow.history.models import Allergy, MedicationStatement
from .models import MedicationOrder, PharmacyDispenseEvent, PharmacyReview
from .pharmacy import pharmacy_command
from .services import MedicationConflict, snapshot, transition_order
from .tests import MedicationFixture


class PharmacyFixture(MedicationFixture):
    def setup_pharmacy(self):
        self.setup_medications()
        group = Group.objects.create(name="Pharmacist")
        self.pharmacist = get_user_model().objects.create_user(username="synthetic-pharmacist")
        self.other_pharmacist = get_user_model().objects.create_user(username="other-pharmacist")
        self.pharmacist.groups.add(group)
        self.other_pharmacist.groups.add(group)
        self.signed = self.sign(self.make_order())

    def pharmacy_action(self, action, version, actor=None, key=None, **data):
        return pharmacy_command(actor or self.pharmacist, self.signed.public_id, action, version,
                                key or uuid.uuid4(), True, **data)


class PharmacyTests(PharmacyFixture, TestCase):
    def setUp(self):
        self.setup_pharmacy()

    def test_unclaimed_queue_has_minimum_information_and_excludes_drafts(self):
        draft = self.make_order(instructions="Private synthetic draft")
        self.client.force_login(self.pharmacist)
        queue = self.client.get(reverse("pharmacy_worklist"))
        self.assertContains(queue, str(self.signed.public_id))
        self.assertNotContains(queue, self.patient.mrn)
        self.assertNotContains(queue, self.signed.instructions)
        self.assertNotContains(queue, str(draft.public_id))
        self.assertEqual(self.client.get(reverse("pharmacy_detail", args=[self.signed.public_id])).status_code, 404)
        claim = self.client.get(reverse("pharmacy_claim", args=[self.signed.public_id]))
        self.assertNotContains(claim, self.patient.mrn)
        self.assertFalse(PharmacyReview.objects.exists())

    def test_claim_is_idempotent_and_only_assignee_can_view(self):
        key = uuid.uuid4()
        for _ in range(2):
            self.pharmacy_action("claim", self.signed.version, key=key)
        review = PharmacyReview.objects.get(order=self.signed)
        self.assertEqual(review.assignee, self.pharmacist)
        self.assertEqual(self.signed.events.filter(audit__action="pharmacy_claim").count(), 1)
        detail = reverse("pharmacy_detail", args=[self.signed.public_id])
        self.client.force_login(self.other_pharmacist)
        self.assertEqual(self.client.get(detail).status_code, 404)
        with self.assertRaises(PermissionDenied):
            self.pharmacy_action("approve", 1, actor=self.other_pharmacist)
        self.client.force_login(self.pharmacist)
        self.assertContains(self.client.get(detail), self.patient.mrn)

    def test_pharmacist_does_not_gain_clinical_or_demographic_access(self):
        self.pharmacy_action("claim", self.signed.version)
        self.client.force_login(self.pharmacist)
        for path in ("/app/patients/", f"/app/patients/{self.patient.pk}/",
                     f"/app/patients/{self.patient.pk}/chart/", reverse("med_detail", args=[self.signed.public_id])):
            self.assertEqual(self.client.get(path).status_code, 403)

    def test_existing_roles_and_csrf_cannot_perform_pharmacy_actions(self):
        url = reverse("pharmacy_claim", args=[self.signed.public_id])
        for actor in self.staff.values():
            self.client.force_login(actor)
            self.assertEqual(self.client.get(url).status_code, 403)
            with self.assertRaises(PermissionDenied):
                self.pharmacy_action("claim", self.signed.version, actor=actor)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.pharmacist)
        self.assertEqual(protected.post(url, {}).status_code, 403)

    def test_clarification_response_is_author_scoped_and_keeps_signature(self):
        before = snapshot(self.signed)
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("clarify", 1, reason="Confirm fictional timing")
        with self.assertRaises(MedicationConflict):
            self.pharmacy_action("approve", 2)
        with self.assertRaises(PermissionDenied):
            self.pharmacy_action("respond", 2, actor=self.other, reason="Wrong physician")
        self.client.force_login(self.physician)
        detail = self.client.get(reverse("med_detail", args=[self.signed.public_id]))
        self.assertContains(detail, "Confirm fictional timing")
        self.assertContains(detail, "Respond to clarification")
        self.pharmacy_action("respond", 2, actor=self.physician, reason="Use the signed fictional instructions")
        self.assertEqual(PharmacyReview.objects.get(order=self.signed).status, "pending")
        self.signed.refresh_from_db()
        self.assertEqual(snapshot(self.signed), before)
        self.assertEqual(self.signed.events.get(audit__action="pharmacy_respond").actor, self.physician)

    def test_rejection_requires_reason_and_blocks_approval_and_dispensing(self):
        self.pharmacy_action("claim", self.signed.version)
        with self.assertRaises(ValidationError):
            self.pharmacy_action("reject", 1)
        self.pharmacy_action("reject", 1, reason="Synthetic review rejection")
        for action in ("approve", "dispense"):
            with self.assertRaises(MedicationConflict):
                self.pharmacy_action(action, 2, quantity=self.signed.quantity)
        self.assertEqual(PharmacyReview.objects.get(order=self.signed).status, "rejected")
        self.assertFalse(PharmacyDispenseEvent.objects.exists())

    def test_dispense_requires_approval_and_exact_quantity(self):
        self.pharmacy_action("claim", self.signed.version)
        with self.assertRaises(MedicationConflict):
            self.pharmacy_action("dispense", 1, quantity=self.signed.quantity)
        self.pharmacy_action("approve", 1)
        for invalid in (0, True, 1, self.signed.quantity + 1):
            with self.subTest(quantity=invalid), self.assertRaises(ValidationError):
                self.pharmacy_action("dispense", 2, quantity=invalid)

    def test_dispense_replay_preserves_independent_states_and_provenance(self):
        before = snapshot(self.signed)
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("approve", 1)
        key = uuid.uuid4()
        for _ in range(2):
            self.pharmacy_action("dispense", 2, key=key, quantity=self.signed.quantity)
        dispense = PharmacyDispenseEvent.objects.get()
        self.assertEqual(dispense.quantity, self.signed.quantity)
        self.assertEqual(dispense.event.actor, self.pharmacist)
        self.assertEqual(dispense.event.audit.patient, self.patient)
        self.assertEqual(dispense.review.status, "approved")
        self.signed.refresh_from_db()
        self.assertEqual(snapshot(self.signed), before)
        with self.assertRaises(MedicationConflict):
            self.pharmacy_action("dispense", 3, quantity=self.signed.quantity)
        with self.assertRaises(ValidationError):
            dispense.save()

    def test_stale_review_and_claimed_cancellation_are_denied(self):
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("clarify", 1, reason="Check fiction")
        with self.assertRaises(MedicationConflict):
            self.pharmacy_action("respond", 1, actor=self.physician, reason="Stale")
        with self.assertRaises(MedicationConflict):
            transition_order(self.physician, self.signed.public_id, "cancel", self.signed.version, uuid.uuid4(),
                             True, reason="Cancellation after claim")

    def test_completed_encounter_processing_preserves_soap_and_history(self):
        self.finish_encounter()
        soap = Note.objects.values().get(encounter=self.encounter)
        clinical_history = (list(Allergy.objects.values()), list(MedicationStatement.objects.values()))
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("clarify", 1, reason="Clarify completed visit")
        self.pharmacy_action("respond", 2, actor=self.physician, reason="Fictional response")
        self.pharmacy_action("approve", 3)
        self.pharmacy_action("dispense", 4, quantity=self.signed.quantity)
        self.assertEqual(Note.objects.values().get(encounter=self.encounter), soap)
        self.assertEqual((list(Allergy.objects.values()), list(MedicationStatement.objects.values())), clinical_history)
        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.status, "completed")

    def test_completed_encounter_rejects_inconsistent_signature_time(self):
        self.finish_encounter()
        # Simulate inconsistent imported metadata in this isolated test only.
        MedicationOrder.objects.filter(pk=self.signed.pk).update(signed_at=self.encounter.completed_at)
        with self.assertRaises(MedicationConflict):
            self.pharmacy_action("claim", self.signed.version)
        self.assertFalse(PharmacyReview.objects.exists())

    def test_dispense_audit_failure_rolls_back_quantity_and_version(self):
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("approve", 1)
        with patch("careflow.medications.services.AuditEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.pharmacy_action("dispense", 2, quantity=self.signed.quantity)
        self.assertFalse(PharmacyDispenseEvent.objects.exists())
        self.assertEqual(PharmacyReview.objects.get().version, 2)


class PharmacyConcurrencyTests(PharmacyFixture, TransactionTestCase):
    def compete(self, action, version, actors, **data):
        barrier = Barrier(2)

        def attempt(actor_id):
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=actor_id)
                barrier.wait(timeout=10)
                self.pharmacy_action(action, version, actor=actor, **data)
                return True
            except MedicationConflict:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [actor.pk for actor in actors]))
        self.assertEqual(sorted(results), [False, True])

    def test_competing_claim_creates_one_assignment(self):
        self.setup_pharmacy()
        self.compete("claim", self.signed.version, [self.pharmacist, self.other_pharmacist])
        self.assertEqual(PharmacyReview.objects.count(), 1)

    def test_competing_cancellation_and_claim_cannot_both_commit(self):
        self.setup_pharmacy()
        barrier = Barrier(2)

        def attempt(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                operation()
                return True
            except MedicationConflict:
                return False
            finally:
                close_old_connections()

        def cancel():
            transition_order(self.physician, self.signed.public_id, "cancel", self.signed.version,
                             uuid.uuid4(), True, reason="Synthetic race")

        def claim():
            self.pharmacy_action("claim", self.signed.version)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [cancel, claim]))
        self.assertEqual(sorted(results), [False, True])
        self.signed.refresh_from_db()
        self.assertEqual(PharmacyReview.objects.exists(), self.signed.status == "signed")

    def test_competing_dispense_creates_one_immutable_receipt(self):
        self.setup_pharmacy()
        self.pharmacy_action("claim", self.signed.version)
        self.pharmacy_action("approve", 1)
        self.compete("dispense", 2, [self.pharmacist, self.pharmacist], quantity=self.signed.quantity)
        self.assertEqual(PharmacyDispenseEvent.objects.count(), 1)
