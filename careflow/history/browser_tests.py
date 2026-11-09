import os
import secrets
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from careflow.clinical.models import Encounter
from careflow.patients.models import Patient
from careflow.scheduling.models import Appointment
from .models import AllergyState, EncounterDiagnosis, MedicalHistory, MedicationStatement, Problem


class HistoryBrowserTests(StaticLiveServerTestCase):
    def test_longitudinal_history_and_encounter_diagnosis(self):
        from playwright.sync_api import expect, sync_playwright

        password = secrets.token_urlsafe(24)
        physician = get_user_model().objects.create_user(username="history.browser", password=password)
        physician.groups.add(Group.objects.get_or_create(name="Physician")[0])
        patient = Patient.objects.create(mrn="HISTORY-BROWSER", first_name="Synthetic", last_name="HistoryBrowser",
                                         dob=date(1980, 1, 1), sex="unknown")
        now = timezone.now()
        appointment = Appointment.objects.create(patient=patient, physician=physician, start_at=now,
            end_at=now + timedelta(minutes=30), status="arrived", appointment_type="Synthetic history")
        output = os.environ.get("CAREFLOW_BROWSER_SCREENSHOT_DIR")
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(self.live_server_url + "/login/")
            page.get_by_label("Username").fill(physician.username)
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.wait_for_url("**/app/dashboard/")
            page.goto(self.live_server_url + f"/app/appointments/{appointment.pk}/start/")
            page.get_by_role("button", name="Confirm encounter start").click()
            page.wait_for_url("**/encounters/*/")
            expect(page.get_by_role("link", name="Medical history", exact=True)).to_be_visible()
            encounter_url = page.url

            def create(kind, label, extra):
                page.get_by_role("link", name=kind, exact=True).click()
                page.get_by_role("link", name="Add " + kind.lower(), exact=True).click()
                page.locator("#id_label").fill(label)
                page.locator("#id_source").select_option("patient_reported")
                for field, value in extra.items():
                    locator = page.locator("#id_" + field)
                    if locator.evaluate("el => el.tagName") == "SELECT":
                        locator.select_option(value)
                    else:
                        locator.fill(value)
                page.locator("#id_synthetic_confirmed").check()
                page.get_by_role("button", name="Save record", exact=True).click()
                expect(page.get_by_role("heading", name=label, exact=True)).to_be_visible()

            create("Medical history", "Synthetic prior procedure", {"category": "surgical", "start_date": "2010-01-01"})
            page.get_by_role("link", name="Edit record", exact=True).click()
            page.locator("#id_comments").fill("Revised synthetic surgical history")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save record", exact=True).click()
            page.get_by_label("I reviewed this synthetic record and its provenance.").check()
            page.get_by_role("button", name="Record review", exact=True).click()
            expect(page.locator("dl").get_by_text("Revised synthetic surgical history", exact=True)).to_be_visible()
            create("Problems", "Synthetic longitudinal problem", {})
            page.get_by_role("link", name="Allergies", exact=True).click()
            page.locator("#id_status").select_option("no_known")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Record allergy assessment").click()
            expect(page.get_by_role("heading", name="Allergy assessment: No known allergies")).to_be_visible()
            create("Allergies", "Synthetic allergen", {"reaction": "Synthetic reaction", "severity": "mild"})
            page.get_by_role("link", name="Allergies", exact=True).click()
            expect(page.get_by_role("heading", name="Allergy assessment: Documented allergies")).to_be_visible()
            # The navigation label is Medications; the module heading is Medication history.
            page.get_by_role("link", name="Medications", exact=True).click()
            page.get_by_role("link", name="Add medication history", exact=True).click()
            for field, value in {"label": "Synthetic medication statement", "dose": "Mock dose description",
                                 "route": "Mock route", "frequency": "Mock frequency"}.items():
                page.locator("#id_" + field).fill(value)
            page.locator("#id_source").select_option("documented")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save record", exact=True).click()
            expect(page.get_by_role("heading", name="Synthetic medication statement", exact=True)).to_be_visible()
            page.goto(encounter_url)
            page.get_by_role("link", name="Encounter diagnoses", exact=True).click()
            page.get_by_role("link", name="Add encounter diagnoses", exact=True).click()
            page.locator("#id_label").fill("Synthetic primary diagnosis")
            page.locator("#id_rank").select_option("primary")
            page.locator("#id_source").select_option("documented")
            page.locator("#id_problem").select_option(label="Synthetic longitudinal problem (Active)")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save record", exact=True).click()
            expect(page.get_by_role("heading", name="Synthetic primary diagnosis", exact=True)).to_be_visible()
            if output:
                page.screenshot(path=str(Path(output) / "history-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), page.evaluate("window.innerWidth"))
            if output:
                page.screenshot(path=str(Path(output) / "history-mobile.png"), full_page=True)
            page.get_by_role("link", name="Chart overview", exact=True).click()
            expect(page.get_by_text("history_diagnoses_create", exact=True)).to_be_visible()
            browser.close()
        self.assertEqual(MedicalHistory.objects.get().category, "surgical")
        self.assertIsNotNone(MedicalHistory.objects.get().reviewed_at)
        self.assertEqual(AllergyState.objects.get().status, "documented")
        self.assertEqual(MedicationStatement.objects.get().source, "documented")
        self.assertEqual(EncounterDiagnosis.objects.get().problem, Problem.objects.get())
        self.assertEqual(Encounter.objects.count(), 1)
