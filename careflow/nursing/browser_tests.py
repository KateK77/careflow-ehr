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
from .models import NursingEvent, RoomingAssessment, VitalObservation


class NursingBrowserTests(StaticLiveServerTestCase):
    def test_rooming_vitals_correction_flowsheet_and_physician_review(self):
        from playwright.sync_api import expect, sync_playwright

        password = secrets.token_urlsafe(24)
        staff = {}
        for role in ["Nurse", "Physician"]:
            user = get_user_model().objects.create_user(username="browser-" + role.lower(), password=password)
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            staff[role] = user
        patient = Patient.objects.create(mrn="NURSING-BROWSER", first_name="Synthetic", last_name="Rooming",
                                         dob=date(1980, 1, 1), sex="unknown")
        now = timezone.now()
        appointment = Appointment.objects.create(patient=patient, physician=staff["Physician"], start_at=now,
            end_at=now + timedelta(minutes=30), status="arrived", checked_in_at=now,
            checked_in_by=staff["Nurse"], appointment_type="Synthetic nursing")
        output = os.environ.get("CAREFLOW_BROWSER_SCREENSHOT_DIR")
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def login(username):
                page.goto(self.live_server_url + "/login/")
                page.get_by_label("Username").fill(username)
                page.get_by_label("Password").fill(password)
                page.get_by_role("button", name="Sign in to workspace").click()
                page.wait_for_url("**/app/dashboard/")

            login(staff["Nurse"].username)
            page.get_by_role("link", name="Nursing workspace", exact=True).click()
            page.locator("#id_q").fill(patient.mrn)
            page.locator("#id_status").select_option("arrived")
            page.get_by_role("button", name="Filter worklist").click()
            for width in [1440, 700, 390]:
                page.set_viewport_size({"width": width, "height": 1000})
                expect(page.get_by_role('cell', name=patient.mrn, exact=False)).to_be_visible()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), page.evaluate('window.innerWidth'))
            expect(page.locator('.scroll-hint').first).to_be_visible()
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.get_by_role("link", name="Nursing record", exact=True).click()
            page.get_by_role("link", name="Record assessment", exact=True).click()
            page.locator("#id_chief_complaint").fill("Synthetic rooming complaint")
            page.locator("#id_pain_score").fill("0")
            page.locator("#id_observations").fill("Fictional nursing observations only")
            page.locator("#id_ready_for_provider").check()
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save nursing documentation").click()
            page.wait_for_url("**/assessment/*/")
            expect(page.locator('dl').get_by_text("Ready for provider", exact=True)).to_be_visible()
            page.get_by_role("link", name="Appointment nursing record", exact=True).click()
            page.get_by_role("link", name="Record vitals", exact=True).click()
            for field, value in {"systolic": "120", "diastolic": "80", "heart_rate": "70", "respiratory_rate": "16",
                                 "temperature": "37.2", "oxygen_saturation": "98", "height": "170", "weight": "70", "pain_score": "0"}.items():
                page.locator("#id_" + field).fill(value)
            for field, value in {"temperature_unit": "C", "height_unit": "cm", "weight_unit": "kg", "source": "measured"}.items():
                page.locator("#id_" + field).select_option(value)
            page.locator("#id_observed_at").fill(timezone.localtime(now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M"))
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save nursing documentation").click()
            page.wait_for_url("**/vitals/*/")
            first_record_url = page.url
            page.reload()
            expect(page.locator("dl").get_by_text("37.20 °C", exact=True)).to_be_visible()
            page.get_by_role("link", name="Correct documentation", exact=True).click()
            page.locator("#id_heart_rate").fill("71")
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save nursing documentation").click()
            expect(page.get_by_role("heading", name="Vital observation corrected", exact=True)).to_be_visible()
            page.locator('details').first.locator('summary').click()
            expect(page.locator('details').first.locator('table')).to_have_class('audit-table')
            page.get_by_role("link", name="Appointment nursing record", exact=True).click()
            page.get_by_role("link", name="Record vitals", exact=True).click()
            page.locator("#id_pain_score").fill("3")
            page.locator("#id_source").select_option("patient_reported")
            page.locator("#id_observed_at").fill(timezone.localtime(now - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M"))
            page.locator("#id_synthetic_confirmed").check()
            page.get_by_role("button", name="Save nursing documentation").click()
            page.wait_for_url("**/vitals/*/")
            page.get_by_role("link", name="Nursing flowsheet", exact=True).click()
            expect(page.locator(".flowsheet thead th")).to_have_count(3)
            expect(page.get_by_role("cell", name="71 beats/min", exact=True)).to_be_visible()
            expect(page.get_by_role("cell", name="37.20 °C", exact=True)).to_be_visible()
            if output:
                page.screenshot(path=str(Path(output) / "nursing-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), page.evaluate("window.innerWidth"))
            if output:
                page.screenshot(path=str(Path(output) / "nursing-mobile.png"), full_page=True)
            page.get_by_role("button", name="Sign out", exact=True).click()
            login(staff["Physician"].username)
            page.goto(first_record_url)
            expect(page.locator("dl").get_by_text("71 beats/min", exact=True)).to_be_visible()
            expect(page.get_by_role("link", name="Correct documentation", exact=True)).to_have_count(0)
            page.get_by_role("link", name="Chart overview", exact=True).click()
            expect(page.get_by_role("heading", name="Nursing rooming and latest vital signs")).to_be_visible()
            expect(page.get_by_text("Vital observation corrected", exact=True)).to_be_visible()
            self.assertEqual(errors, [])
            browser.close()
        self.assertTrue(RoomingAssessment.objects.get().ready_for_provider)
        self.assertEqual(VitalObservation.objects.count(), 2)
        self.assertEqual(VitalObservation.objects.order_by("pk").first().heart_rate, 71)
        self.assertEqual(NursingEvent.objects.count(), 4)
        self.assertFalse(Encounter.objects.exists())
