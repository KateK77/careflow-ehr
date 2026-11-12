"""HTTP contracts for specialist and patient session boundaries."""
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from careflow.patients.models import Patient
from careflow.portal.models import PatientPortalAccount


class WorkspaceBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {}
        for role in ("Administrator", "Physician", "Nurse", "FrontDesk", "BillingStaff",
                     "RadiologyStaff", "Pharmacist", "Lab Staff", "HospitalOperations", "patient"):
            actor = get_user_model().objects.create_user(username=role.lower().replace(" ", "-"))
            cls.users[role] = actor
            if role != "patient":
                actor.groups.add(Group.objects.create(name=role))
        patient = Patient.objects.create(
            mrn="SYN-BOUNDARY", first_name="Synthetic", last_name="Boundary",
            dob=date(1980, 1, 1), sex="unknown",
        )
        PatientPortalAccount.objects.create(user=cls.users["patient"], patient=patient)


# Each row names one endpoint and distinct roles whose access is intentionally
# allowed or denied. This covers empty workspaces as well as writable entry pages.
WORKSPACE_ACCESS = {
    "patient_create": (("Administrator", "FrontDesk"), ("Physician", "Nurse", "BillingStaff", "patient")),
    "appointment_create": (("Administrator", "FrontDesk"), ("Nurse", "Physician", "RadiologyStaff", "patient")),
    "physician_workspace": (("Administrator", "Physician", "Nurse"), ("FrontDesk", "Pharmacist", "Lab Staff", "patient")),
    "nursing_workspace": (("Nurse", "Physician"), ("FrontDesk", "HospitalOperations", "BillingStaff", "patient")),
    "lab_catalog_create": (("Administrator",), ("Nurse", "Physician", "Lab Staff", "patient")),
    "pharmacy_worklist": (("Pharmacist",), ("Administrator", "RadiologyStaff", "Lab Staff", "patient")),
    "mar_worklist": (("Administrator", "Physician", "Nurse"), ("FrontDesk", "Pharmacist", "BillingStaff", "patient")),
    "imaging_catalog": (("Administrator",), ("Physician", "Nurse", "RadiologyStaff", "patient")),
    "imaging_workspace": (("RadiologyStaff",), ("Administrator", "Lab Staff", "HospitalOperations", "patient")),
    "billing_worklist": (("BillingStaff",), ("Administrator", "FrontDesk", "RadiologyStaff", "patient")),
    "billing_claims": (("BillingStaff",), ("Nurse", "Physician", "Pharmacist", "patient")),
    "hospital_admissions": (("HospitalOperations", "Administrator"), ("Nurse", "Physician", "FrontDesk", "patient")),
    "hospital_capacity": (("HospitalOperations", "Administrator"), ("Nurse", "Pharmacist", "Lab Staff", "patient")),
    "ed_board": (("HospitalOperations", "Nurse", "Physician"), ("FrontDesk", "BillingStaff", "RadiologyStaff", "patient")),
    "staff_portal_messages": (("Physician",), ("Administrator", "Nurse", "FrontDesk", "patient")),
    "staff_portal_requests": (("Administrator", "FrontDesk"), ("Physician", "Nurse", "HospitalOperations", "patient")),
    "portal_home": (("patient",), ("Administrator", "BillingStaff", "RadiologyStaff", "HospitalOperations")),
}


def workspace_case(route, role, status):
    def verify(self):
        self.client.force_login(self.users[role])
        response = self.client.get(reverse(route))
        self.assertEqual(response.status_code, status)
    return verify


for route, (allowed, denied) in WORKSPACE_ACCESS.items():
    for status, roles in ((200, allowed), (403, denied)):
        for role in roles:
            slug = role.lower().replace(" ", "_")
            policy = "permits" if status == 200 else "denies"
            name = f"test_{route}_{policy}_{slug}"
            test = workspace_case(route, role, status)
            test.__name__ = name
            setattr(WorkspaceBoundaryTests, name, test)
