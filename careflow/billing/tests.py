import secrets
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from careflow.portal.tests import PortalFixture
from .models import BillingEvent, PatientStatement
from .services import change_statement, create_catalog, create_coverage


class BillingFixture(PortalFixture):
    def setup_billing(self):
        self.setup_portal()
        self.billing_password = secrets.token_urlsafe(25)
        self.biller = get_user_model().objects.create_user("synthetic-biller", password=self.billing_password)
        self.biller.groups.add(Group.objects.create(name="BillingStaff"))
        self.code = {"code": "SYN-VISIT", "description": "Synthetic visit charge", "unit_cents": 1255}
        self.catalog_item = create_catalog(self.biller, self.code, 0, uuid.uuid4())

    def change(self, action, version, key=None, **values):
        return change_statement(self.biller, self.encounter.pk, version, key or uuid.uuid4(), action, **values)

    def add(self, version=0, key=None, quantity=3):
        return self.change("billing_charge_add", version, key, catalog_id=self.catalog_item.pk, quantity=quantity)

    def released(self):
        self.finish_encounter()
        self.add()
        self.change("billing_finalize", 1)
        return self.change("billing_release", 2)

    def coverage_data(self):
        return {"policy": "SYN-POLICY", "payer": "Synthetic Pine", "coverage_type": "group",
                "status": "active", "effective_from": timezone.localdate() - timedelta(days=30), "effective_to": None}


class BillingTests(BillingFixture, TestCase):
    def setUp(self):
        self.setup_billing()

    def test_completed_only_and_minimum_staff_role(self):
        with self.assertRaises(ValidationError):
            self.add()
        self.finish_encounter()
        route = reverse("billing_encounter", args=[self.encounter.pk])
        for actor in [self.admin, self.physician, self.staff["Nurse"], self.staff["FrontDesk"], self.lab, self.portal_a]:
            self.client.force_login(actor)
            self.assertEqual(self.client.get(route).status_code, 403)
            self.assertEqual(self.client.post(route, {}).status_code, 403)
        with self.assertRaises(PermissionDenied):
            create_catalog(self.admin, self.code, 0, uuid.uuid4())
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.biller)
        self.assertEqual(client.post(route, {}).status_code, 403)

    def test_catalog_revision_does_not_reprice_existing_charge(self):
        self.finish_encounter()
        draft = self.add()
        revised = create_catalog(self.biller, {**self.code, "unit_cents": 9999}, 1, uuid.uuid4())
        self.assertEqual(revised.revision, 2)
        with self.assertRaises(ValidationError):
            self.add(1)
        self.assertEqual(draft.charges.get().subtotal_cents, 3765)
        with self.assertRaises(ValidationError):
            create_catalog(self.biller, {**self.code, "unit_cents": 10.5}, 2, uuid.uuid4())

    def test_version_replay_edit_void_and_immutable_snapshot(self):
        self.finish_encounter()
        key = uuid.uuid4()
        item = self.add(key=key)
        self.assertEqual(self.add(key=key).pk, item.pk)
        with self.assertRaises(ValidationError):
            self.add(key=key, quantity=2)
        with self.assertRaises(ValidationError):
            self.add()
        first = item.charges.get()
        self.change("billing_charge_edit", 1, charge_id=first.pk, quantity=2)
        self.add(2, quantity=1)
        second = item.charges.exclude(pk=first.pk).get()
        self.change("billing_charge_void", 3, charge_id=second.pk)
        finalized = self.change("billing_finalize", 4)
        self.assertEqual(finalized.total_cents, 2510)
        snapshot = finalized.lines.get()
        self.assertEqual(snapshot.subtotal_cents, 2510)
        with self.assertRaises(ValidationError):
            snapshot.save()
        with self.assertRaises(ValidationError):
            self.change("billing_charge_edit", 5, charge_id=first.pk, quantity=4)
        self.assertEqual(BillingEvent.objects.filter(subject="statement").count(), 5)

    def test_patient_portal_release_and_cross_patient_denial(self):
        self.finish_encounter()
        item = self.add()
        route = reverse("portal_statement", args=[item.pk])
        self.client.force_login(self.portal_a)
        self.assertEqual(self.client.get(route).status_code, 404)
        self.change("billing_finalize", 1)
        self.assertEqual(self.client.get(route).status_code, 404)
        self.change("billing_release", 2)
        self.assertContains(self.client.get(route), "$37.65")
        self.assertNotContains(self.client.get(route), "Billing history")
        self.client.force_login(self.portal_b)
        self.assertEqual(self.client.get(route).status_code, 404)
        self.assertEqual(self.client.post(route, {}).status_code, 405)

    def test_coverage_validation_revisions_and_ownership(self):
        data = self.coverage_data()
        create_coverage(self.biller, self.patient.pk, data, 0, uuid.uuid4())
        for patient, changes in [(self.foreign, {}), (self.patient, {"effective_to": data["effective_from"] - timedelta(days=1)})]:
            with self.assertRaises(ValidationError):
                create_coverage(self.biller, patient.pk, {**data, **changes}, 1, uuid.uuid4())
        current = create_coverage(self.biller, self.patient.pk, {**data, "status": "historical"}, 1, uuid.uuid4())
        self.assertEqual(current.revision, 2)
        self.client.force_login(self.portal_b)
        self.assertNotContains(self.client.get(reverse("portal_billing")), data["payer"])

    def test_audit_failure_rolls_back_charge_statement_and_snapshots(self):
        self.finish_encounter()
        with patch("careflow.billing.services.BillingEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                self.add()
        self.assertFalse(PatientStatement.objects.exists())
        item = self.add()
        with patch("careflow.billing.services.BillingEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                self.change("billing_finalize", 1)
        item.refresh_from_db()
        self.assertEqual(item.status, "draft")
        self.assertFalse(item.lines.exists())
