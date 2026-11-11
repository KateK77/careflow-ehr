import secrets
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
from careflow.portal.tests import PortalFixture
from .models import HospitalEvent, InpatientStay
from .services import add_facility, available_beds, change_stay, decide_admission, request_admission


class HospitalFixture(PortalFixture):
    def setup_hospital(self):
        self.setup_portal()
        self.password = self.password or secrets.token_urlsafe(25)
        for actor in (self.admin, self.physician):
            actor.set_password(self.password)
            actor.save(update_fields=["password"])
        self.operator = get_user_model().objects.create_user("synthetic-operations", password=self.password)
        self.operator.groups.add(Group.objects.create(name="HospitalOperations"))
        self.department = self.facility("department", "Synthetic Hospital")
        self.ward = self.facility("ward", "Synthetic Ward A", self.department, "inpatient")
        self.room = self.facility("room", "Room A", self.ward)
        self.bed = self.facility("bed", "Bed 1", self.room)
        ward = self.facility("ward", "Synthetic Ward B", self.department, "inpatient")
        room = self.facility("room", "Room B", ward)
        self.destination = self.facility("bed", "Bed 2", room)

    def facility(self, kind, name, parent=None, ward_kind=None):
        return add_facility(self.admin, kind, name, parent.pk if parent else None, ward_kind, uuid.uuid4())

    def admission_request(self, patient=None, key=None):
        return request_admission(self.operator, (patient or self.patient).pk, "Synthetic admission", key or uuid.uuid4())

    def admit(self, item, bed=None, key=None):
        return decide_admission(self.operator, item.pk, item.version, key or uuid.uuid4(), "hospital_admit", True,
                                bed_id=(bed or self.bed).pk, attending_id=self.physician.pk)

    def change(self, item, action, actor=None, **data):
        return change_stay(actor or self.operator, item.request.patient_id, item.pk, item.version, uuid.uuid4(),
                           action, True, **data)


class HospitalTests(HospitalFixture, TestCase):
    def setUp(self):
        self.setup_hospital()

    def test_admit_transfer_discharge_and_signed_note_preservation(self):
        self.finish_encounter()
        before = Note.objects.filter(encounter=self.encounter).values().get()
        item = self.admit(self.admission_request())
        self.assertFalse(available_beds().filter(pk=self.bed.pk).exists())
        item = self.change(item, "hospital_transfer", bed_id=self.destination.pk, note="Synthetic transfer")
        with self.assertRaises(ValidationError):
            self.change(item, "hospital_discharge", note="No plan yet")
        item = self.change(item, "hospital_discharge_plan", self.physician, note="Synthetic planning")
        item = self.change(item, "hospital_discharge", note="Synthetic summary")
        self.assertEqual(item.status, "discharged")
        self.assertEqual(set(available_beds()), {self.bed, self.destination})
        transfers = list(item.events.values_list("previous_bed_id", "next_bed_id"))
        self.assertIn((self.bed.pk, self.destination.pk), transfers)
        self.assertIn((self.destination.pk, None), transfers)
        self.assertEqual(Note.objects.filter(encounter=self.encounter).values().get(), before)
        with self.assertRaises(ValidationError):
            self.change(item, "hospital_transfer", bed_id=self.bed.pk, note="Closed stay")

    def test_duplicate_patient_bed_replay_and_stale(self):
        key = uuid.uuid4()
        first = self.admission_request(key=key)
        self.assertEqual(first.pk, self.admission_request(key=key).pk)
        with self.assertRaises(ValidationError):
            self.admission_request()
        stay = self.admit(first)
        with self.assertRaises(ValidationError):
            self.admission_request()
        other = self.admission_request(self.foreign)
        with self.assertRaises(ValidationError):
            self.admit(other)
        self.change(stay, "hospital_transfer", bed_id=self.destination.pk, note="Synthetic transfer")
        with self.assertRaises(ValidationError):
            self.change(stay, "hospital_discharge_plan", self.physician, note="Stale")

    def test_scoped_access_and_audit_atomicity(self):
        request = self.admission_request()
        with patch("careflow.hospital.services.HospitalEvent.objects.create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                self.admit(request)
        self.assertFalse(InpatientStay.objects.exists())
        stay = self.admit(request)
        route = reverse("hospital_stay", args=[self.patient.pk, stay.pk])
        wrong = reverse("hospital_stay", args=[self.foreign.pk, stay.pk])
        for role in ("BillingStaff", "RadiologyStaff", "Pharmacist"):
            user = get_user_model().objects.create_user(role)
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            self.client.force_login(user)
            self.assertEqual(self.client.get(route).status_code, 403)
        for actor, code in [(self.other, 404), (self.portal_a, 403), (self.staff["FrontDesk"], 403)]:
            self.client.force_login(actor)
            self.assertEqual(self.client.get(route).status_code, code)
        self.client.force_login(self.staff["Nurse"])
        self.assertContains(self.client.get(route), "Stay details")
        self.assertEqual(self.client.post(route, {"action": "hospital_transfer"}).status_code, 403)
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(wrong).status_code, 404)
        self.assertEqual(self.client.post(wrong, {}).status_code, 404)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.operator)
        self.assertEqual(protected.post(route, {}).status_code, 403)
        with self.assertRaises(PermissionDenied):
            self.change(stay, "hospital_discharge_plan", self.other, note="Wrong clinician")
        event = HospitalEvent.objects.filter(stay=stay).first()
        with self.assertRaises(ValidationError):
            event.save()


class HospitalConcurrencyTests(HospitalFixture, TransactionTestCase):
    def test_competing_bed_allocations(self):
        self.setup_hospital()
        items = [self.admission_request(), self.admission_request(self.foreign)]
        barrier = Barrier(2)

        def compete(item):
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                self.admit(item)
                return True
            except ValidationError:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(compete, items)).count(True), 1)
        self.assertEqual(InpatientStay.objects.filter(bed=self.bed, status="active").count(), 1)
