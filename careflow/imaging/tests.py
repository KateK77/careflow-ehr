import secrets
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from careflow.labs.tests import LabFixture
from .models import ImagingCatalog, ImagingEvent, ImagingOrder
from .services import active_catalog, catalog_revision, order_command


class ImagingFixture(LabFixture):
    def setup_imaging(self):
        self.make_fixture()
        self.password = secrets.token_urlsafe(24)
        for actor in (self.admin, self.physician):
            actor.set_password(self.password)
            actor.save(update_fields=["password"])
        self.catalog_data = {"code": "SYN-XR-DEMO", "name": "Synthetic X-ray", "modality": "XR", "active": True}
        self.catalog_item = catalog_revision(self.admin, self.catalog_data, 0, uuid.uuid4())

    def imaging(self, action, order=None, key=None, **data):
        return order_command(self.physician, self.patient.pk, self.encounter.pk, action,
                             order.version if order else 0, key or uuid.uuid4(), True,
                             order_id=order.pk if order else None, **data)

    def draft_order(self, order=None, key=None, indication="Synthetic draft indication"):
        return self.imaging("imaging_draft", order, key, catalog_id=self.catalog_item.pk,
                            priority="routine", indication=indication)


class ImagingOrderTests(ImagingFixture, TestCase):
    def setUp(self):
        self.setup_imaging()

    def test_catalog_creation_and_identical_command_replay(self):
        self.client.force_login(self.admin)
        url = reverse("imaging_catalog")
        payload = {**self.catalog_data, "code": "SYN-US-NEW", "modality": "US", "version": 0, "key": uuid.uuid4()}
        for _ in range(2):
            self.assertRedirects(self.client.post(url, payload), url, fetch_redirect_response=False)
        revision = ImagingCatalog.objects.get(code=payload["code"])
        self.assertEqual((revision.revision, revision.modality), (1, "US"))
        self.assertEqual(ImagingEvent.objects.filter(catalog=revision).count(), 1)

    def test_catalog_stale_edit_preserves_the_newer_revision(self):
        self.client.force_login(self.admin)
        url = reverse("imaging_catalog")
        payload = {**self.catalog_data, "version": 1}
        newer = {**payload, "name": "Synthetic updated name", "key": uuid.uuid4()}
        self.assertRedirects(self.client.post(url, newer), url, fetch_redirect_response=False)
        stale = {**payload, "name": "Synthetic stale name", "key": uuid.uuid4()}
        response = self.client.post(url, stale)
        self.assertContains(response, "The submitted revision for SYN-XR-DEMO is stale.", status_code=400)
        self.assertContains(response, "Latest revision is 2.", status_code=400)
        self.assertContains(response, f'<a href="{url}">Reload the imaging catalog</a>', status_code=400, html=True)
        self.assertContains(response, "reapply your changes", status_code=400)
        self.assertEqual(list(ImagingCatalog.objects.filter(code=payload["code"]).values_list("revision", "name")),
                         [(2, newer["name"]), (1, payload["name"])])
        self.assertFalse(ImagingEvent.objects.filter(key=stale["key"]).exists())

    def test_catalog_deactivation_preserves_revision_and_draft_requires_current(self):
        draft = self.draft_order()
        with self.assertRaises(PermissionDenied):
            catalog_revision(self.physician, self.catalog_data, 1, uuid.uuid4())
        revised = catalog_revision(self.admin, {**self.catalog_data, "active": False}, 1, uuid.uuid4())
        self.assertEqual(revised.revision, 2)
        self.assertFalse(active_catalog().exists())
        with self.assertRaises(ValidationError):
            self.imaging("imaging_sign", draft)
        self.assertTrue(draft.catalog.active)
        with self.assertRaises(ValidationError):
            draft.catalog.save()

    def test_draft_edit_sign_schedule_cancel_and_history(self):
        key = uuid.uuid4()
        original = self.draft_order(key=key)
        self.assertEqual(self.draft_order(key=key).pk, original.pk)
        with self.assertRaises(ValidationError):
            self.draft_order(key=key, indication="Changed")
        edited = self.draft_order(original, indication="Edited fictional indication")
        with self.assertRaises(ValidationError):
            self.imaging("imaging_sign", original)
        signed = self.imaging("imaging_sign", edited)
        self.finish_encounter()
        slot = timezone.now() + timedelta(days=2)
        scheduled = self.imaging("imaging_schedule", signed, scheduled_at=slot)
        self.assertEqual(scheduled.exam.scheduled_at, slot)
        cancelled = self.imaging("imaging_cancel", scheduled, reason="Synthetic cancellation")
        self.assertEqual(cancelled.signed_at, signed.signed_at)
        self.assertEqual(cancelled.status, "cancelled")
        self.assertEqual(cancelled.events.count(), 5)

    def test_roles_scoped_post_and_csrf(self):
        draft = self.draft_order()
        route = reverse("imaging_order", args=[draft.pk])
        for actor in [self.other, self.staff["Nurse"], self.admin, self.staff["FrontDesk"]]:
            self.client.force_login(actor)
            self.assertEqual(self.client.get(route).status_code, 404)
            self.assertEqual(self.client.post(route, {}).status_code, 404)
        signed = self.imaging("imaging_sign", draft)
        self.client.force_login(self.staff["Nurse"])
        self.assertContains(self.client.get(route), "Synthetic X-ray")
        self.assertEqual(self.client.post(route, {}).status_code, 403)
        self.client.force_login(self.physician)
        wrong = reverse("imaging_order_new", args=[self.foreign.pk, self.encounter.pk])
        self.assertEqual(self.client.get(wrong).status_code, 404)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.physician)
        self.assertEqual(protected.post(route, {}).status_code, 403)
        self.assertEqual(signed.encounter.patient_id, self.patient.pk)

    def test_completed_encounter_blocks_draft_and_sign_and_audit_rollback(self):
        with patch("careflow.imaging.services.ImagingEvent.objects.create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                self.draft_order()
        self.assertFalse(ImagingOrder.objects.exists())
        draft = self.draft_order()
        self.finish_encounter()
        with self.assertRaises(ValidationError):
            self.draft_order()
        with self.assertRaises(ValidationError):
            self.imaging("imaging_sign", draft)
