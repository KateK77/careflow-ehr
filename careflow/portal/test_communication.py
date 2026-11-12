import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from careflow.scheduling.models import Appointment
from careflow.scheduling.services import save_appointment
from .communication import mark_read, reply, review_request, start_thread, submit_request
from .models import PatientAppointmentRequest, PatientPortalEvent
from .tests import PortalFixture


class PortalCommunicationTests(PortalFixture, TestCase):
    def setUp(self):
        self.setup_portal()
        self.slot = (timezone.now() + timedelta(days=4)).replace(minute=0, second=0, microsecond=0)

    def start(self, key=None):
        return start_thread(self.portal_a, self.physician.pk, "Synthetic question", "Fictional patient message",
                            key or uuid.uuid4())

    def request_slot(self, kind="new", target=None, key=None, start=None):
        return submit_request(self.portal_a, kind, self.physician.pk, target.pk if target else None,
                              start or self.slot, 20, "Synthetic request", key or uuid.uuid4())

    def review(self, item, decision="approved", version=1, key=None, actor=None):
        return review_request(actor or self.admin, item.pk, self.physician.pk, decision, version,
                              "Synthetic staff response", key or uuid.uuid4(), True)

    def scheduled(self, patient=None, start=None):
        return save_appointment(self.admin, {
            "patient": patient or self.patient, "physician": self.physician,
            "start_at": start or self.slot, "duration": 20, "appointment_type": "Synthetic check",
            "reason": "", "version": None,
        })

    def test_conversation_exchange_unread_and_command_replay(self):
        key = uuid.uuid4()
        thread = self.start(key)
        self.assertEqual(self.start(key).pk, thread.pk)
        staff = reverse("staff_portal_thread", args=[thread.pk])
        self.client.force_login(self.physician)
        self.assertContains(self.client.get(reverse("staff_portal_messages")), "Unread")
        read_key = uuid.uuid4()
        mark_read(self.physician, thread.pk, self.physician.pk, False, 1, read_key)
        mark_read(self.physician, thread.pk, self.physician.pk, False, 1, read_key)
        self.assertNotContains(self.client.get(reverse("staff_portal_messages")), "Unread")
        payload = {"version": 1, "body": "Synthetic physician reply", "key": str(uuid.uuid4())}
        self.assertEqual(self.client.post(staff, payload).status_code, 302)
        self.assertEqual(self.client.post(staff, payload).status_code, 302)
        self.assertEqual(self.client.post(staff, {**payload, "key": str(uuid.uuid4())}).status_code, 409)
        self.client.force_login(self.portal_a)
        self.assertContains(self.client.get(reverse("portal_home")), "Unread conversations (1)")
        self.assertContains(self.client.get(reverse("portal_thread", args=[thread.pk])), "Synthetic physician reply")
        mark_read(self.portal_a, thread.pk, self.physician.pk, True, 2, uuid.uuid4())
        self.assertContains(self.client.get(reverse("portal_home")), "Unread conversations (0)")
        self.assertEqual(thread.messages.count(), 2)
        self.assertEqual(thread.events.count(), 4)
        self.assertTrue(all(event.audit.patient_id == self.patient.pk for event in thread.events.all()))

    def test_message_scope_direct_get_post_csrf_and_no_staff_forgery(self):
        thread = self.start()
        patient_path = reverse("portal_thread", args=[thread.pk])
        staff_path = reverse("staff_portal_thread", args=[thread.pk])
        for actor, path, status in [
            (self.portal_b, patient_path, 404), (self.portal_a, staff_path, 403),
            (self.other, staff_path, 404), (self.admin, staff_path, 403),
        ]:
            self.client.force_login(actor)
            self.assertEqual(self.client.get(path).status_code, status)
            self.assertEqual(self.client.post(path, {}).status_code, status)
        with self.assertRaises(PermissionDenied):
            reply(self.portal_a, thread.pk, self.physician.pk, False, "Forged staff reply", 1, uuid.uuid4())
        with self.assertRaises(ValidationError):
            start_thread(self.portal_a, self.other.pk, "Invalid clinician", "Synthetic message", uuid.uuid4())
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.portal_a)
        self.assertEqual(protected.post(patient_path, {}).status_code, 403)
        self.assertEqual(thread.messages.count(), 1)

    def test_new_request_approval_is_atomic_and_idempotent(self):
        count = Appointment.objects.count()
        key = uuid.uuid4()
        item = self.request_slot(key=key)
        self.assertEqual(self.request_slot(key=key).pk, item.pk)
        self.assertEqual(Appointment.objects.count(), count)
        with self.assertRaises(ValidationError):
            self.request_slot()
        review_key = uuid.uuid4()
        approved = self.review(item, key=review_key)
        self.assertEqual(self.review(item, key=review_key).resulting_appointment_id, approved.resulting_appointment_id)
        self.assertEqual(Appointment.objects.count(), count + 1)
        self.assertEqual(approved.resulting_appointment.patient_id, self.patient.pk)
        self.assertEqual(approved.events.count(), 2)
        with self.assertRaises(ValidationError):
            self.review(item)
        self.client.force_login(self.portal_a)
        response = self.client.get(reverse("portal_request", args=[item.pk]))
        self.assertContains(response, "Synthetic staff response")
        self.assertContains(response, "Current appointment status")
        self.assertContains(response, "Approved")

    def test_reschedule_and_cancel_use_scheduling_service(self):
        target = self.scheduled()
        moved = self.request_slot("reschedule", target, start=self.slot + timedelta(hours=1))
        self.assertEqual(self.review(moved).resulting_appointment_id, target.pk)
        target.refresh_from_db()
        self.assertEqual(target.start_at, self.slot + timedelta(hours=1))
        cancelled = self.request_slot("cancel", target)
        self.review(cancelled)
        target.refresh_from_db()
        self.assertEqual(target.status, "cancelled")
        self.assertTrue(target.events.filter(audit__action="appointment_cancel").exists())

    def test_conflict_stale_target_and_started_encounter_cannot_be_approved(self):
        target = self.scheduled()
        item = self.request_slot()
        with self.assertRaises(ValidationError):
            self.review(item)
        item.refresh_from_db()
        self.assertEqual(item.status, "pending")
        self.assertEqual(self.review(item, "rejected").status, "rejected")
        request = self.request_slot("cancel", target)
        Appointment.objects.filter(pk=target.pk).update(version=2)
        with self.assertRaises(ValidationError):
            self.review(request)
        Appointment.objects.filter(pk=target.pk).update(version=1)
        self.encounter.appointment = target
        self.encounter.save(update_fields=["appointment"])
        with self.assertRaises(ValidationError):
            self.review(request)
        target.refresh_from_db()
        self.assertEqual(target.status, "scheduled")

    def test_cross_patient_request_and_role_denials(self):
        target = self.scheduled(self.foreign)
        with self.assertRaises(ValidationError):
            self.request_slot("cancel", target)
        item = self.request_slot(start=self.slot + timedelta(hours=1))
        path = reverse("portal_request", args=[item.pk])
        staff = reverse("staff_portal_request", args=[item.pk])
        self.client.force_login(self.portal_b)
        self.assertEqual(self.client.get(path).status_code, 404)
        self.client.force_login(self.portal_a)
        self.assertEqual(self.client.post(staff, {}).status_code, 403)
        self.assertEqual(self.client.post(reverse("portal_request_new", args=["cancel"]), {
            "appointment": target.pk, "explanation": "Wrong patient", "key": str(uuid.uuid4()),
        }).status_code, 400)
        for actor in (self.physician, self.staff["Nurse"], self.staff["Lab Staff"]):
            self.client.force_login(actor)
            self.assertEqual(self.client.get(staff).status_code, 403)
            self.assertEqual(self.client.post(staff, {}).status_code, 403)
            with self.assertRaises(PermissionDenied):
                self.review(item, actor=actor)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.admin)
        self.assertEqual(protected.post(staff, {}).status_code, 403)
        protected.force_login(self.portal_a)
        self.assertEqual(protected.post(reverse("portal_request_new", args=["new"]), {}).status_code, 403)
        self.assertEqual(PatientAppointmentRequest.objects.count(), 1)

    def test_request_review_rolls_back_schedule_and_audit(self):
        item = self.request_slot()
        count = Appointment.objects.count()
        audits = PatientPortalEvent.objects.count()
        with patch("careflow.portal.communication.PatientPortalEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                self.review(item)
        item.refresh_from_db()
        self.assertEqual(item.status, "pending")
        self.assertEqual(Appointment.objects.count(), count)
        self.assertEqual(PatientPortalEvent.objects.count(), audits)

    def test_message_audit_failure_rolls_back_reply(self):
        thread = self.start()
        with patch("careflow.portal.communication.PatientPortalEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                reply(self.physician, thread.pk, self.physician.pk, False, "Synthetic reply", 1, uuid.uuid4())
        thread.refresh_from_db()
        self.assertEqual(thread.version, 1)
        self.assertEqual(thread.messages.count(), 1)
