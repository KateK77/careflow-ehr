import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from careflow.clinical.models import Note
from careflow.history.models import MedicationStatement
from careflow.labs.tests import LabFixture
from .models import MedicationOrder, MedicationOrderEvent
from .services import MedicationConflict, create_catalog, review_token, save_draft, set_active, transition_order


class MedicationFixture(LabFixture):
    def setup_medications(self):
        self.make_fixture()
        self.catalog_data = dict(code="SYN-AMBER", revision=1, name="Synthetic Amber",
                                 dosage_form="demo_tablet", strength="10 demo units", route="oral", frequency="daily")
        self.medication = create_catalog(self.admin, self.catalog_data, uuid.uuid4(), True)
        self.medication = set_active(self.admin, self.medication.pk, True, 1, uuid.uuid4(), True)

    def order_data(self):
        return dict(catalog_id=self.medication.pk, dose="1 demo units", route="oral", frequency="daily",
                    duration=2, quantity=2, instructions="Synthetic instructions")

    def make_order(self, **overrides):
        return save_draft(self.physician, self.encounter.pk, self.patient.pk,
                          {**self.order_data(), **overrides}, 0, uuid.uuid4(), True)

    def sign(self, order, key=None):
        return transition_order(self.physician, order.public_id, "sign", order.version,
                                key or uuid.uuid4(), True, review_token(self.physician, order))


class MedicationTests(MedicationFixture, TestCase):
    def setUp(self):
        self.setup_medications()

    def test_catalog_revision_activation_and_snapshot(self):
        draft = self.make_order()
        signed = self.sign(draft)
        second = create_catalog(self.admin, {**self.catalog_data, "revision": 2, "strength": "20 demo units"},
                                uuid.uuid4(), True)
        with self.assertRaises(ValidationError):
            set_active(self.admin, second.pk, True, 1, uuid.uuid4(), True)
        set_active(self.admin, self.medication.pk, False, 2, uuid.uuid4(), True)
        set_active(self.admin, second.pk, True, 1, uuid.uuid4(), True)
        signed.refresh_from_db()
        self.assertEqual(signed.catalog_snapshot["strength"], "10 demo units")
        second.name = "Synthetic replacement"
        with self.assertRaises(ValidationError):
            second.save()

    def test_catalog_rejects_nonfictional_configuration(self):
        for changes in ({"code": "REAL"}, {"strength": "10 mg"}, {"name": "Medication"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                create_catalog(self.admin, {**self.catalog_data, **changes}, uuid.uuid4(), True)
        with self.assertRaises(PermissionDenied):
            create_catalog(self.physician, self.catalog_data, uuid.uuid4(), True)

    def test_draft_edit_and_stale_preview(self):
        draft = self.make_order()
        token = review_token(self.physician, draft)
        changed = save_draft(self.physician, self.encounter.pk, self.patient.pk,
                             {**self.order_data(), "quantity": 4}, 1, uuid.uuid4(), True, draft.public_id)
        self.assertEqual((changed.version, changed.quantity), (2, 4))
        with self.assertRaises(MedicationConflict):
            transition_order(self.physician, draft.public_id, "sign", 2, uuid.uuid4(), True, token)
        self.assertEqual(changed.events.count(), 2)

    def test_order_validation_and_wrong_patient(self):
        with self.assertRaises(PermissionDenied):
            save_draft(self.physician, self.encounter.pk, self.foreign.pk, self.order_data(), 0, uuid.uuid4(), True)
        for data in ({"route": "topical"}, {"duration": 0}, {"dose": "2 mg"}):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                self.make_order(**data)

    def test_signed_order_is_immutable_and_cancel_retains_signature(self):
        order = self.sign(self.make_order())
        signature = order.signed_at
        order.instructions = "Rewritten"
        with self.assertRaises(ValidationError):
            order.save()
        with self.assertRaises(ValidationError):
            transition_order(self.physician, order.public_id, "cancel", order.version, uuid.uuid4(), True)
        cancelled = transition_order(self.physician, order.public_id, "cancel", order.version, uuid.uuid4(),
                                     True, reason="Synthetic cancellation")
        self.assertEqual((cancelled.status, cancelled.signed_at), ("cancelled", signature))
        self.assertEqual(cancelled.instructions, "Synthetic instructions")

    def test_replay_requires_identical_command_and_no_duplicate_signature(self):
        key = uuid.uuid4()
        args = (self.physician, self.encounter.pk, self.patient.pk, self.order_data(), 0, key, True)
        order = save_draft(*args)
        self.assertEqual(save_draft(*args).pk, order.pk)
        with self.assertRaises(MedicationConflict):
            save_draft(*args[:3], {**self.order_data(), "quantity": 4}, *args[4:])
        sign_key = uuid.uuid4()
        self.sign(order, sign_key)
        self.sign(order, sign_key)
        self.assertEqual(order.events.count(), 2)

    def test_role_and_csrf_boundaries(self):
        draft = self.make_order()
        url = reverse("med_detail", args=[draft.public_id])
        for actor in (self.admin, self.staff["Nurse"], self.other, self.staff["FrontDesk"], self.staff["Lab Staff"]):
            self.client.force_login(actor)
            self.assertIn(self.client.get(url).status_code, {403, 404})
            with self.assertRaises(PermissionDenied):
                transition_order(actor, draft.public_id, "sign", draft.version, uuid.uuid4(), True)
        self.sign(draft)
        self.client.force_login(self.staff["Nurse"])
        self.assertContains(self.client.get(url), "Synthetic Amber")
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.physician)
        self.assertEqual(protected.post(reverse("med_sign", args=[draft.public_id]), {}).status_code, 403)

    def test_audit_failure_rolls_back_order_and_command(self):
        with patch("careflow.medications.services.AuditEvent.objects.create", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaises(RuntimeError):
                self.make_order()
        self.assertFalse(MedicationOrder.objects.exists())
        self.assertFalse(MedicationOrderEvent.objects.filter(order__isnull=False).exists())

    def test_completion_blocks_signing_and_preserves_clinical_data(self):
        draft = self.make_order()
        signed = self.sign(self.make_order())
        self.finish_encounter()
        note_before = Note.objects.values().get(encounter=self.encounter)
        history_before = list(MedicationStatement.objects.values())
        with self.assertRaises(MedicationConflict):
            self.sign(draft)
        with self.assertRaises(MedicationConflict):
            self.make_order()
        transition_order(self.physician, signed.public_id, "cancel", signed.version, uuid.uuid4(),
                         True, reason="Late synthetic cancellation")
        self.assertEqual(Note.objects.values().get(encounter=self.encounter), note_before)
        self.assertEqual(list(MedicationStatement.objects.values()), history_before)
        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.status, "completed")

    def test_review_sign_and_chart_pages(self):
        order = self.make_order()
        self.client.force_login(self.physician)
        url = reverse("med_sign", args=[order.public_id])
        preview = self.client.get(url)
        self.assertContains(preview, "Historical allergy assessment")
        self.assertContains(preview, "Synthetic instructions")
        form = preview.context["form"]
        response = self.client.post(url, {**form.initial, "key": str(uuid.uuid4()), "confirmed": True})
        self.assertRedirects(response, reverse("med_detail", args=[order.public_id]))
        history = self.client.get(reverse("med_history", args=[self.patient.pk]))
        self.assertContains(history, "Synthetic Amber")
        self.assertContains(history, "Signed")


class MedicationConcurrencyTests(MedicationFixture, TransactionTestCase):
    def test_competing_sign_commands_create_one_signature(self):
        self.setup_medications()
        order = self.make_order()
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=self.physician.pk)
                barrier.wait(timeout=10)
                transition_order(actor, order.public_id, "sign", order.version, uuid.uuid4(), True,
                                 review_token(actor, order))
                return True
            except MedicationConflict:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(order.events.filter(audit__action="med_order_sign").count(), 1)
