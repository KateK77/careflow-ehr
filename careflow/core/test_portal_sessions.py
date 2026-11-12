"""Real credential submissions for staff workspace routing and session isolation."""
import secrets
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientPortalAccount


class PortalSessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(24)
        cls.actors = {}
        for role in STAFF_DESTINATIONS:
            actor = get_user_model().objects.create_user(role.lower().replace(" ", "-"), password=cls.password)
            actor.groups.add(Group.objects.create(name=role))
            cls.actors[role] = actor
        cls.patient_login = get_user_model().objects.create_user("synthetic-patient", password=cls.password)
        patient = Patient.objects.create(mrn="SYN-SESSION", first_name="Synthetic", last_name="Session",
                                         dob=date(1980, 1, 1), sex="unknown")
        PatientPortalAccount.objects.create(user=cls.patient_login, patient=patient)

    def test_inactive_patient_cannot_open_portal_session(self):
        self.patient_login.is_active = False
        self.patient_login.save(update_fields=["is_active"])
        response = self.client.post(reverse("portal_login"),
                                    {"username": self.patient_login.username, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_withdrawal_of_role_takes_effect_in_existing_session(self):
        actor = self.actors["BillingStaff"]
        self.client.force_login(actor)
        url = reverse("billing_worklist")
        self.assertEqual(self.client.get(url).status_code, 200)
        actor.groups.clear()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_patient_session_cannot_post_to_admission_worklist(self):
        self.client.force_login(self.patient_login)
        self.assertEqual(self.client.post(reverse("hospital_admissions"), {"reason": "Synthetic"}).status_code, 403)


STAFF_DESTINATIONS = {
    "Administrator": "dashboard",
    "Physician": "dashboard",
    "Nurse": "dashboard",
    "FrontDesk": "dashboard",
    "BillingStaff": "billing_worklist",
    "RadiologyStaff": "imaging_workspace",
    "Pharmacist": "pharmacy_worklist",
    "Lab Staff": "lab_worklist",
    "HospitalOperations": "hospital_dashboard",
}


def staff_login_case(role, destination):
    def verify(self):
        actor = self.actors[role]
        response = self.client.post(reverse("login"), {"username": actor.username, "password": self.password})
        self.assertRedirects(response, reverse(destination))
        self.assertEqual(AuditEvent.objects.get(actor=actor, action="login").outcome, "success")
        self.assertEqual(self.client.get(reverse("portal_home")).status_code, 403)
    return verify


for role, destination in STAFF_DESTINATIONS.items():
    name = "test_staff_sign_in_routes_" + role.lower().replace(" ", "_")
    test = staff_login_case(role, destination)
    test.__name__ = name
    setattr(PortalSessionTests, name, test)
