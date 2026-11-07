import os
import re
import secrets
from io import StringIO
from unittest.mock import patch

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings

from .models import AuditEvent, Patient


@override_settings(DEBUG=True)
class PatientBrowserTests(StaticLiveServerTestCase):
    """Optional headless check. Install playwright and Chromium before running this module."""

    def test_registration_workflow_at_desktop_and_mobile_widths(self):
        from playwright.sync_api import sync_playwright

        password = secrets.token_urlsafe(24)
        with patch.dict(os.environ, {
            "CAREFLOW_ALLOW_DEMO_SEED": "1", "CAREFLOW_DEMO_PASSWORD": password,
        }):
            call_command("seed_synthetic", stdout=StringIO())
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(self.live_server_url + "/login/")
            page.get_by_label("Username").fill("frontdesk.demo")
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.wait_for_url("**/app/dashboard/")
            page.get_by_role("link", name="Patients", exact=True).click()
            page.wait_for_url("**/app/patients/")
            page.get_by_label("Search patients").fill("DEMO-0001")
            page.get_by_role("button", name="Search", exact=True).click()
            self.assertEqual(page.locator("tbody tr").count(), 1)
            page.get_by_role("link", name="Register patient", exact=False).last.click()
            page.get_by_label("MRN *", exact=True).fill("BROWSER-001")
            page.get_by_label("First name *", exact=True).fill("Browser")
            page.get_by_label("Last name *", exact=True).fill("Synthetic")
            page.get_by_label("Date of birth *", exact=True).fill("1990-05-20")
            page.get_by_label("Sex *", exact=True).select_option("unknown")
            page.get_by_label("I confirm this record contains synthetic data only.").check()
            page.get_by_role("button", name="Save patient").click()
            page.wait_for_url(re.compile(r"/app/patients/\d+/$"))
            self.assertIn("Synthetic patient record saved.", page.inner_text("body"))
            page.get_by_role("link", name="Edit demographics").click()
            page.get_by_label("Phone", exact=True).fill("202-555-0101")
            page.get_by_label("I confirm this record contains synthetic data only.").check()
            page.get_by_role("button", name="Save patient").click()
            page.wait_for_url(re.compile(r"/app/patients/\d+/$"))
            self.assertIn("202-555-0101", page.inner_text("body"))
            page.get_by_role("link", name="Patients", exact=True).click()
            output = os.environ.get("CAREFLOW_BROWSER_SCREENSHOT_DIR")
            if output:
                os.makedirs(output, exist_ok=True)
                page.screenshot(path=os.path.join(output, "patients-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertLessEqual(
                page.evaluate("document.documentElement.scrollWidth"),
                page.evaluate("window.innerWidth"),
            )
            if output:
                page.screenshot(path=os.path.join(output, "patients-mobile.png"), full_page=True)
            page.get_by_role("button", name="Sign out").click()
            page.wait_for_url("**/login/")
            self.assertEqual(errors, [])
            browser.close()
        patient = Patient.objects.get(mrn="BROWSER-001")
        self.assertEqual(patient.phone, "202-555-0101")
        self.assertTrue(AuditEvent.objects.filter(patient=patient, action="patient_update").exists())
