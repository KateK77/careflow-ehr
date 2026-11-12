import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from careflow.clinical.models import Note
from .emergency import advance_ed, register_ed
from .models import AdmissionRequest, EmergencyVisit, InpatientStay
from .tests import HospitalFixture


class EDFixture(HospitalFixture):
    def setup_ed(self):
        self.setup_hospital()
        self.nurse = self.staff["Nurse"]
        self.nurse.set_password(self.password)
        self.nurse.save(update_fields=["password"])
        ward = self.facility("ward", "Synthetic Emergency", self.department, "ed")
        self.ed_room = self.facility("room", "ED Room 1", ward)

    def arrival(self, patient=None, key=None):
        return register_ed(self.operator, (patient or self.patient).pk, "walk_in",
                           "Synthetic complaint", key or uuid.uuid4(), True)

    def advance(self, visit, action, actor=None, key=None, **data):
        return advance_ed(actor or self.operator, visit.patient_id, visit.pk, action, visit.version,
                          key or uuid.uuid4(), True, **data)

    def triage(self, visit):
        return self.advance(visit, "ed_triage", self.nurse, category="demo_b", note="Synthetic triage")

    def room_visit(self, visit):
        return self.advance(visit, "ed_room", self.nurse, room_id=self.ed_room.pk, clinician_id=self.physician.pk)

    def provider_visit(self):
        roomed = self.room_visit(self.triage(self.arrival()))
        return self.advance(roomed, "ed_provider", self.physician)


class EmergencyTests(EDFixture, TestCase):
    def setUp(self):
        self.setup_ed()

    def test_transition_order_triage_history_and_room_release(self):
        key = uuid.uuid4()
        waiting = self.arrival(key=key)
        self.assertEqual(self.arrival(key=key).pk, waiting.pk)
        with self.assertRaises(ValidationError):
            self.arrival()
        with self.assertRaises(ValidationError):
            self.room_visit(waiting)
        triaged = self.triage(waiting)
        second = self.advance(triaged, "ed_triage", self.nurse, category="demo_c", note="Synthetic update")
        with self.assertRaises(ValidationError):
            self.room_visit(triaged)
        roomed = self.room_visit(second)
        other = self.triage(self.arrival(self.foreign))
        with self.assertRaises(ValidationError):
            self.room_visit(other)
        provider = self.advance(roomed, "ed_provider", self.physician)
        observed = self.advance(provider, "ed_observation", self.physician)
        final = self.advance(observed, "ed_discharge", self.physician, note="Synthetic discharge")
        self.assertIsNone(final.room)
        self.assertEqual(final.status, "discharged")
        self.assertEqual(final.events.filter(audit__action="ed_triage").count(), 2)
        self.assertEqual(self.room_visit(other).room, self.ed_room)

    def test_ed_admission_reuses_admission_policy_and_preserves_soap(self):
        self.finish_encounter()
        before = Note.objects.filter(encounter=self.encounter).values().get()
        visit = self.provider_visit()
        with self.assertRaises(ValidationError):
            self.admission_request()
        with self.assertRaises(PermissionDenied):
            self.advance(visit, "ed_admit", self.nurse, bed_id=self.bed.pk, note="Synthetic admission")
        key = uuid.uuid4()
        admitted = self.advance(visit, "ed_admit", key=key, bed_id=self.bed.pk, note="Synthetic admission")
        replay = self.advance(visit, "ed_admit", key=key, bed_id=self.bed.pk, note="Synthetic admission")
        self.assertEqual(replay.inpatient_stay_id, admitted.inpatient_stay_id)
        self.assertEqual(admitted.inpatient_stay.request.patient_id, visit.patient_id)
        self.assertEqual(admitted.inpatient_stay.bed, self.bed)
        self.assertEqual(admitted.inpatient_stay.attending, self.physician)
        self.assertEqual(admitted.status, "admitted")
        self.assertIsNone(admitted.room)
        self.assertEqual(InpatientStay.objects.count(), 1)
        self.assertEqual(Note.objects.filter(encounter=self.encounter).values().get(), before)

    def test_occupied_bed_and_failed_audit_roll_back_disposition(self):
        self.admit(self.admission_request(self.foreign))
        visit = self.provider_visit()
        with self.assertRaises(ValidationError):
            self.advance(visit, "ed_admit", bed_id=self.bed.pk, note="Synthetic occupied bed")
        self.assertFalse(AdmissionRequest.objects.filter(patient=self.patient).exists())
        with patch("careflow.hospital.emergency.record", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                self.advance(visit, "ed_admit", bed_id=self.destination.pk, note="Synthetic audit failure")
        visit.refresh_from_db()
        self.assertEqual(visit.status, "provider")
        self.assertEqual(visit.room, self.ed_room)
        self.assertFalse(AdmissionRequest.objects.filter(patient=self.patient).exists())

    def test_role_scope_wrong_patient_and_chart_visibility(self):
        visit = self.provider_visit()
        route = reverse("ed_visit", args=[self.patient.pk, visit.pk])
        wrong = reverse("ed_visit", args=[self.foreign.pk, visit.pk])
        for role in ("RadiologyStaff", "BillingStaff", "Pharmacist"):
            actor = get_user_model().objects.create_user(role)
            group, _ = Group.objects.get_or_create(name=role)
            actor.groups.add(group)
            self.client.force_login(actor)
            self.assertEqual(self.client.get(route).status_code, 403)
        for actor, code in [(self.other, 404), (self.portal_a, 403), (self.staff["FrontDesk"], 403)]:
            self.client.force_login(actor)
            self.assertEqual(self.client.get(route).status_code, code)
            self.assertEqual(self.client.post(route, {"action": "ed_discharge"}).status_code, code)
        self.client.force_login(self.nurse)
        self.assertEqual(self.client.post(route, {"action": "ed_discharge"}).status_code, 403)
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(wrong).status_code, 404)
        self.assertEqual(self.client.post(wrong, {"action": "ed_admit"}).status_code, 404)
        self.client.force_login(self.physician)
        self.assertContains(self.client.get(reverse("patient_chart", args=[self.patient.pk])), f"ED Visit #{visit.pk}")
        self.assertEqual(EmergencyVisit.objects.get().status, "provider")
