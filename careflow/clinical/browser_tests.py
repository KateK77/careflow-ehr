import os
import re
import secrets
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from careflow.patients.models import Patient
from careflow.scheduling.models import Appointment
from .models import Encounter, Note


class ClinicalBrowserTests(StaticLiveServerTestCase):
    """Optional real Chromium workflow; never uses the local application database."""

    def test_physician_draft_sign_and_complete(self):
        from playwright.sync_api import expect, sync_playwright

        password = secrets.token_urlsafe(24)
        physician = get_user_model().objects.create_user(username="clinical.browser", password=password)
        physician.groups.add(Group.objects.get_or_create(name="Physician")[0])
        patient = Patient.objects.create(mrn="BROWSER-CHART", first_name="Synthetic", last_name="Browser",
                                         dob=date(1980, 1, 1), sex="unknown")
        now = timezone.now()
        appointment = Appointment.objects.create(patient=patient, physician=physician, start_at=now,
            end_at=now + timedelta(minutes=30), status="arrived", checked_in_at=now,
            checked_in_by=physician, appointment_type="Synthetic browser workflow")
        output = os.environ.get("CAREFLOW_BROWSER_SCREENSHOT_DIR")
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(self.live_server_url + "/login/")
            page.get_by_label("Username").fill("clinical.browser")
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.wait_for_url("**/app/dashboard/")
            page.get_by_role("link", name="Physician workspace", exact=True).click()
            page.get_by_role("link", name="Start encounter", exact=True).click()
            page.get_by_role("button", name="Confirm encounter start").click()
            page.get_by_role("link", name="Create SOAP draft").click()
            for label in ["Subjective", "Objective", "Assessment", "Plan"]:
                page.get_by_label(re.compile("^" + label + ":?$")).fill("Synthetic " + label.lower() + " content")
            page.get_by_label("I confirm this note contains synthetic information only.").check()
            page.get_by_role("button", name="Save draft", exact=True).click()
            page.reload()
            expect(page.get_by_text("Synthetic subjective content", exact=True)).to_be_visible()
            page.get_by_role("link", name="Edit SOAP draft").click()
            expect(page.get_by_label(re.compile("^Subjective:?$"))).to_have_value("Synthetic subjective content")
            page.get_by_label(re.compile("^Plan:?$" )).fill("Revised synthetic plan")
            page.get_by_label("I confirm this note contains synthetic information only.").check()
            page.get_by_role("button", name="Save draft", exact=True).click()
            page.get_by_role("link", name="Review and sign", exact=True).click()
            page.get_by_label("I have reviewed all four sections", exact=False).check()
            page.get_by_role("button", name="Confirm and sign note").click()
            expect(page.get_by_text("Signed — read-only", exact=True)).to_be_visible()
            expect(page.get_by_role("link", name="Edit SOAP draft")).to_have_count(0)
            if output:
                page.screenshot(path=str(Path(output) / "clinical-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), page.evaluate("window.innerWidth"))
            if output:
                page.screenshot(path=str(Path(output) / "clinical-mobile.png"), full_page=True)
            page.get_by_role("button", name="Complete encounter", exact=True).click()
            expect(page.locator(".patient-banner .tag")).to_have_text("Completed")
            page.get_by_role("link", name="Chart overview", exact=True).click()
            expect(page.get_by_role("heading", name="Clinical timeline")).to_be_visible()
            expect(page.get_by_text("note_sign", exact=True)).to_be_visible()
            self.assertEqual(errors, [])
            browser.close()
        encounter = Encounter.objects.get(appointment=appointment)
        note = Note.objects.get(encounter=encounter)
        self.assertEqual(encounter.status, "completed")
        self.assertEqual(note.plan, "Revised synthetic plan")
        self.assertIsNotNone(note.signed_at)
