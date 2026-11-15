"""V2 read models, role boundaries, and isolated preview allocation."""
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from careflow.patients.models import AuditEvent, Patient
from careflow.portal.models import PatientPortalAccount
from careflow.scheduling.models import Appointment
from tools.v2_preview import allocate_database


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class V2DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = {}
        for role in ("Physician", "FrontDesk", "Nurse", "Lab Staff"):
            user = get_user_model().objects.create_user("v2-" + role.replace(" ", ""))
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            cls.users[role] = user
        cls.other = get_user_model().objects.create_user("v2-other-physician")
        cls.other.groups.add(Group.objects.get(name="Physician"))
        cls.patient = Patient.objects.create(mrn="SYN-V2-001", first_name="Fictional",
                                             last_name="Demo", dob=date(1990, 1, 1), sex="unknown")
        cls.portal = get_user_model().objects.create_user("v2-patient")
        PatientPortalAccount.objects.create(user=cls.portal, patient=cls.patient)

    def appointment(self, physician=None, hour=9, day=0, status="scheduled"):
        start = timezone.make_aware(datetime.combine(timezone.localdate(), datetime.min.time()))
        start += timedelta(days=day, hours=hour)
        return Appointment.objects.create(patient=self.patient,
            physician=physician or self.users["Physician"], start_at=start,
            end_at=start + timedelta(minutes=30), appointment_type="Synthetic visit", status=status)

    def dashboard(self, role):
        self.client.force_login(self.users[role])
        return self.client.get("/app/dashboard/")

    def test_physician_agenda_excludes_other_physician(self):
        own = self.appointment()
        unrelated = self.appointment(self.other)
        response = self.dashboard("Physician")
        self.assertEqual(response.context["today_count"], 1)
        self.assertEqual(list(response.context["today_appointments"]), [own])
        self.assertNotContains(response, f'/app/appointments/{unrelated.pk}/')
        self.assertContains(response, f'/app/appointments/{own.pk}/')

    def test_front_desk_counts_current_states_and_excludes_other_dates(self):
        self.appointment(status="arrived")
        self.appointment(self.other, status="cancelled")
        self.appointment(hour=10, day=1)
        self.appointment(hour=11, day=-1)
        response = self.dashboard("FrontDesk")
        self.assertEqual(response.context["today_count"], 2)
        self.assertEqual(response.context["arrived_count"], 1)
        self.assertEqual(response.context["patient_count"], 1)
        self.assertContains(response, "Cancelled")

    def test_agenda_first_eight_sorted_but_total_is_complete(self):
        for hour in reversed(range(8, 18)):
            self.appointment(hour=hour)
        response = self.dashboard("Nurse")
        agenda = list(response.context["today_appointments"])
        self.assertEqual(response.context["today_count"], 10)
        self.assertEqual(len(agenda), 8)
        self.assertEqual([timezone.localtime(a.start_at).hour for a in agenda], list(range(8, 16)))

    def test_dashboard_does_not_write_clinical_or_scheduling_state(self):
        appointment = self.appointment()
        before = (list(Appointment.objects.values()), list(AuditEvent.objects.values()))
        self.dashboard("FrontDesk")
        self.assertEqual(before, (list(Appointment.objects.values()), list(AuditEvent.objects.values())))
        appointment.refresh_from_db()
        self.assertEqual(appointment.version, 1)

    def test_lab_staff_cannot_read_demographics_dashboard(self):
        response = self.dashboard("Lab Staff")
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, self.patient.mrn, status_code=403)

    def test_patient_cannot_read_staff_dashboard(self):
        self.client.force_login(self.portal)
        response = self.client.get("/app/dashboard/")
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, self.patient.mrn, status_code=403)

    def test_anonymous_dashboard_redirects_to_real_login(self):
        self.assertRedirects(self.client.get("/app/dashboard/"),
                             "/login/?next=/app/dashboard/")

    def test_patient_dashboard_request_link_uses_real_form(self):
        self.client.force_login(self.portal)
        response = self.client.get("/portal/")
        self.assertContains(response, 'Request an appointment')
        from django.urls import reverse
        url = reverse("portal_request_new", args=["new"])
        self.assertContains(response, f'href="{url}"')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_registration_grouping_keeps_explicit_confirmation(self):
        self.client.force_login(self.users["FrontDesk"])
        response = self.client.get("/app/patients/new/")
        self.assertContains(response, "Patient identity")
        self.assertContains(response, "Contact information")
        self.assertContains(response, "Required before saving")
        self.assertFalse(response.context["form"]["synthetic_only"].value())
        self.assertNotContains(response, 'name="confirm_duplicate"')
        for field in ("mrn", "first_name", "last_name", "dob", "sex", "gender_identity",
                      "phone", "email", "address", "emergency_contact", "version", "synthetic_only"):
            self.assertContains(response, f'name="{field}"')


class V2PreviewAllocationTests(SimpleTestCase):
    def test_each_launch_allocates_an_absent_database_in_a_new_directory(self):
        with TemporaryDirectory() as tmp:
            first, second = allocate_database(Path(tmp)), allocate_database(Path(tmp))
            self.assertNotEqual(first, second)
            self.assertTrue(first.parent.is_dir())
            self.assertFalse(first.exists())
            self.assertFalse(second.exists())

    def test_existing_database_and_inherited_path_remain_untouched(self):
        with TemporaryDirectory() as tmp:
            original = Path(tmp) / "db.sqlite3"
            original.write_bytes(b"preserve synthetic records")
            with patch.dict("os.environ", {"CAREFLOW_DB_PATH": str(original)}):
                new = allocate_database(Path(tmp))
            self.assertNotEqual(new, original)
            self.assertEqual(original.read_bytes(), b"preserve synthetic records")
