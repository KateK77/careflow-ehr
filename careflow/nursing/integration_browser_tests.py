import os
import re
import secrets
from datetime import timedelta
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.utils import timezone

from careflow.clinical.models import Encounter, Note
from careflow.history.models import MedicalHistory
from careflow.patients.models import Patient
from careflow.scheduling.models import Appointment
from .integration_support import IntegrationFixture, TEST_CLINIC_ZONE
from .models import RoomingAssessment, VitalObservation


@override_settings(TIME_ZONE=TEST_CLINIC_ZONE)
class IntegratedOutpatientBrowserTests(IntegrationFixture, StaticLiveServerTestCase):
    """One real UI journey across all roles using only an isolated test database."""

    def test_registration_to_completed_encounter_with_nursing_handoff(self):
        from playwright.sync_api import expect, sync_playwright

        password = secrets.token_urlsafe(24)
        self.make_staff(password)
        start = timezone.localtime(timezone.now() + timedelta(hours=1)).replace(second=0, microsecond=0)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def login(role):
                page.goto(self.live_server_url + "/login/")
                page.get_by_label("Username").fill(self.staff[role].username)
                page.get_by_label("Password").fill(password)
                page.get_by_role("button", name="Sign in to workspace").click()
                page.wait_for_url("**/app/dashboard/")

            def switch(role):
                page.get_by_role("button", name="Sign out", exact=True).click()
                page.wait_for_url("**/login/")
                login(role)

            login("FrontDesk")
            page.get_by_role("link", name="Register patient", exact=False).last.click()
            for label, value in {"MRN *": "INTEGRATED-BROWSER", "First name *": "Synthetic", "Last name *": "IntegratedBrowser",
                                 "Date of birth *": "1985-01-01"}.items():
                page.get_by_label(label, exact=True).fill(value)
            page.get_by_role("group", name="Recorded sex (required)").get_by_role("radio", name="Unknown").check()
            page.get_by_label("I confirm this record contains synthetic data only.").check()
            page.get_by_role("button", name="Save patient").click()
            page.wait_for_url(re.compile(r"/app/patients/\d+/$"))
            page.get_by_role("link", name="Schedule appointment", exact=True).click()
            page.locator("#id_physician").select_option(str(self.staff["Physician"].pk))
            page.locator("#id_start_at").fill(start.strftime("%Y-%m-%dT%H:%M"))
            page.locator("#id_appointment_type").fill("Synthetic integrated visit")
            page.get_by_role("button", name="Review appointment", exact=True).click()
            expect(page.get_by_role("heading", name="Review appointment", exact=True)).to_be_visible()
            page.get_by_role("button", name="Confirm appointment", exact=True).click()
            page.wait_for_url(re.compile(r"/app/appointments/\d+/$"))
            page.get_by_role("button", name="Mark Arrived", exact=True).click()
            expect(page.locator("main .tag").first).to_have_text("Arrived")
            switch("Nurse")
            page.get_by_role("link", name="Nursing workspace", exact=True).click()
            page.locator("#id_q").fill("INTEGRATED-BROWSER")
            page.get_by_role("button", name="Filter worklist", exact=True).click()
            page.get_by_role("link", name="Nursing record", exact=True).click()
            page.get_by_role("link", name="Record assessment", exact=True).click()
            page.locator("#id_chief_complaint").fill("Fictional integrated nursing complaint")
            page.locator("#id_pain_score").fill("2")
            page.locator("#id_ready_for_provider").check()
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save nursing documentation", exact=True).click()
            page.wait_for_url("**/assessment/*/")
            page.get_by_role("link", name="Appointment nursing record", exact=True).click()
            page.get_by_role("link", name="Record vitals", exact=True).click()
            for field, value in {"systolic": "120", "diastolic": "80", "heart_rate": "70", "temperature": "37.2"}.items():
                page.locator("#id_" + field).fill(value)
            page.locator("#id_temperature_unit").select_option("C")
            page.locator("#id_source").select_option("measured")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save nursing documentation", exact=True).click()
            page.wait_for_url("**/vitals/*/")
            switch("Physician")
            page.get_by_role("link", name="Physician workspace", exact=True).click()
            page.get_by_role("link", name="Start encounter", exact=True).click()
            page.get_by_role("button", name="Confirm encounter start", exact=True).click()
            page.wait_for_url(re.compile(r"/app/patients/\d+/encounters/\d+/$"))
            encounter_id = int(page.url.rstrip("/").split("/")[-1])
            expect(page.get_by_text("Fictional integrated nursing complaint", exact=True)).to_be_visible()
            expect(page.get_by_text("37.20 °C", exact=True)).to_be_visible()
            page.get_by_role("link", name="Medical history", exact=True).click()
            page.get_by_role("link", name="Add medical history", exact=True).click()
            page.locator("#id_category").select_option("medical")
            page.locator("#id_label").fill("Fictional integrated medical history")
            page.locator("#id_source").select_option("documented")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save record", exact=True).click()
            page.get_by_label("I reviewed this synthetic record and its provenance.").check()
            page.get_by_role("button", name="Record review", exact=True).click()
            expect(page.get_by_role("heading", name="Medical history review recorded", exact=True)).to_be_visible()
            page.get_by_role("link", name="Chart overview", exact=True).click()
            page.locator("#encounters").get_by_role("link", name=f"Encounter #{encounter_id}", exact=True).click()
            page.get_by_role("link", name="Create SOAP draft", exact=True).click()
            for label in ["Subjective", "Objective", "Assessment", "Plan"]:
                page.get_by_label(re.compile("^" + label + ":?$")).fill("Fictional integrated " + label.lower())
            page.get_by_label("I confirm this note contains synthetic information only.").check()
            page.get_by_role("button", name="Save draft", exact=True).click()
            page.reload()
            page.get_by_role("link", name="Edit SOAP draft", exact=True).click()
            expect(page.get_by_label(re.compile("^Plan:?$"))).to_have_value("Fictional integrated plan")
            page.get_by_label(re.compile("^Plan:?$")).fill("Revised fictional integrated plan")
            page.get_by_label("I confirm this note contains synthetic information only.").check()
            page.get_by_role("button", name="Save draft", exact=True).click()
            page.get_by_role("link", name="Review and sign", exact=True).click()
            page.get_by_label("I have reviewed all four sections", exact=False).check()
            page.get_by_role("button", name="Confirm and sign note", exact=True).click()
            expect(page.get_by_text("Signed — read-only", exact=True)).to_be_visible()
            page.get_by_role("button", name="Complete encounter", exact=True).click()
            expect(page.locator(".patient-banner .tag")).to_have_text("Completed")
            page.get_by_role("link", name="Chart overview", exact=True).click()
            for event in ["Rooming assessment recorded", "Medical history review recorded", "SOAP note signed", "Encounter completed"]:
                expect(page.get_by_text(event, exact=True)).to_be_visible()
            output = os.environ.get("CAREFLOW_BROWSER_SCREENSHOT_DIR")
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(Path(output) / "integrated-completed-chart.png"), full_page=True)
            self.assertEqual(errors, [])
            browser.close()
        patient = Patient.objects.get(mrn="INTEGRATED-BROWSER")
        appointment = Appointment.objects.get(patient=patient)
        encounter = Encounter.objects.get(appointment=appointment)
        self.assertEqual(encounter.status, "completed")
        self.assertEqual(appointment.status, "arrived")
        self.assertEqual(appointment.checked_in_by, self.staff["FrontDesk"])
        self.assertTrue(RoomingAssessment.objects.get().ready_for_provider)
        self.assertIsNone(VitalObservation.objects.get().encounter_id)
        self.assertEqual(Note.objects.get().plan, "Revised fictional integrated plan")
        self.assertIsNotNone(Note.objects.get().signed_at)
        self.assertIsNotNone(MedicalHistory.objects.get().reviewed_at)
