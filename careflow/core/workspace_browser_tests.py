"""Offline Chromium evidence; these are not live native CUA acceptance results."""
import os
import re
import secrets
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.utils import timezone

from careflow.patients.models import Patient
from careflow.portal.models import PatientPortalAccount
from careflow.scheduling.models import Appointment


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class WorkspaceUpgradeBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(24)
        self.staff = {}
        for role in ("FrontDesk", "Physician", "Lab Staff"):
            user = get_user_model().objects.create_user("upgrade-" + role.replace(" ", ""), password=self.password)
            user.groups.add(Group.objects.get_or_create(name=role)[0])
            self.staff[role] = user
        self.patient = Patient.objects.create(mrn="SYN-UPGRADE-001", first_name="Synthetic",
                                             last_name="Workspace", dob=date(1990, 1, 1), sex="unknown")
        self.portal_user = get_user_model().objects.create_user("upgrade-patient", password=self.password)
        PatientPortalAccount.objects.create(user=self.portal_user, patient=self.patient)

    def page(self, browser):
        page = browser.new_page(viewport={"width": 1280, "height": 800}, service_workers="block")
        # These rehearsals require no external assets or network requests.
        page.route("**/*", lambda route: route.continue_()
                   if urlsplit(route.request.url).netloc == urlsplit(self.live_server_url).netloc
                   else route.abort())
        page.set_default_timeout(10000)
        return page

    def login(self, page, role):
        page.goto(self.live_server_url + "/login/")
        page.get_by_label("Username").fill(self.staff[role].username)
        page.get_by_label("Password").fill(self.password)
        page.get_by_role("button", name="Sign in to workspace").click()
        page.wait_for_url(self.live_server_url + ("/app/lab/workspace/" if role == "Lab Staff" else "/app/dashboard/"))

    def capture(self, page, name):
        directory = os.environ.get("CAREFLOW_UPGRADE_SCREENSHOTS")
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(directory) / (name + ".png")))

    def no_overflow(self, page):
        # Wait for document resources and layout, not indefinite network-idle.
        page.wait_for_load_state("load")
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), page.viewport_size["width"])

    def test_appointment_controls_in_initial_viewport_and_real_confirmation(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                self.login(page, "FrontDesk")
                self.capture(page, "staff-workspace-1280")
                page.goto(self.live_server_url + "/app/appointments/new/")
                self.assertFalse(page.locator(".appointment-search").evaluate("el => el.open"))
                for selector in ("#id_patient", "#id_physician", "#id_start_at", "button[value=review]"):
                    box = page.locator(selector).bounding_box()
                    self.assertIsNotNone(box)
                    self.assertGreaterEqual(box["y"], 0)
                    self.assertLessEqual(box["y"] + box["height"], 800)
                self.capture(page, "appointment-1280-initial")
                page.locator(".appointment-search summary").focus()
                page.keyboard.press("Enter")
                expect(page.get_by_label("Find a patient by name or MRN")).to_be_visible()
                page.get_by_label("Find a patient by name or MRN").fill(self.patient.mrn)
                page.get_by_role("button", name="Find patient", exact=True).click()
                expect(page.get_by_label("Find a patient by name or MRN")).to_have_value(self.patient.mrn)
                page.locator(".appointment-search summary").click()
                future = timezone.localtime() + timedelta(days=2)
                page.locator("#id_patient").select_option(str(self.patient.pk))
                page.locator("#id_physician").select_option(str(self.staff["Physician"].pk))
                page.locator("#id_start_at").fill(future.strftime("%Y-%m-%dT%H:%M"))
                page.get_by_role("button", name="Review appointment", exact=True).click()
                expect(page.get_by_role("heading", name="Review appointment")).to_be_visible()
                self.capture(page, "appointment-review-1280")
                page.get_by_role("button", name="Confirm appointment").click()
                page.wait_for_url(re.compile(r"/app/appointments/\d+/$"))
                expect(page.locator("main .tag").first).to_have_text("Scheduled")
                expect(page.get_by_text("Appointment booked", exact=True)).to_be_visible()
                self.capture(page, "appointment-scheduled-1280")
                page.set_viewport_size({"width": 390, "height": 844})
                self.no_overflow(page)
                self.capture(page, "appointment-mobile")
            finally:
                browser.close()
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.patient_id, self.patient.pk)
        self.assertEqual(appointment.physician_id, self.staff["Physician"].pk)
        self.assertEqual(appointment.status, "scheduled")
        self.assertEqual(appointment.events.count(), 1)
        self.assertEqual(appointment.events.get().audit.action, "appointment_create")
        self.assertEqual(appointment.events.get().audit.actor_id, self.staff["FrontDesk"].pk)

    def test_directory_and_demographics_responsive_navigation(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                loaded = set()
                page.on("response", lambda r: loaded.add(r.url) if r.ok else None)
                self.login(page, "FrontDesk")
                page.get_by_role("link", name="Patients", exact=True).click()
                expect(page.locator('.sidebar a[aria-current="page"]')).to_contain_text("Patients")
                self.assertIn(self.live_server_url + "/static/core/workspace.css", loaded)
                for width in (1280, 700, 390, 320):
                    page.set_viewport_size({"width": width, "height": 800})
                    self.no_overflow(page)
                    self.assertLess(page.locator(".directory-table .tag").bounding_box()["height"], 35)
                    expect(page.get_by_role("link", name="View Patient", exact=True)).to_be_visible()
                    self.capture(page, f"directory-{width}")
                page.get_by_role("link", name="View Patient", exact=True).click()
                self.no_overflow(page)
                expect(page.get_by_role("heading", name=str(self.patient))).to_be_visible()
                self.capture(page, "demographics-320")
            finally:
                browser.close()

    def test_lab_brand_returns_to_authorized_worklist(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                self.login(page, "Lab Staff")
                expect(page.locator(".identity")).to_contain_text("Lab Staff")
                expect(page.locator(".identity")).not_to_contain_text("No staff role")
                page.locator(".brand").click()
                expect(page).to_have_url(self.live_server_url + "/app/lab/workspace/")
                self.capture(page, "laboratory-workspace-1280")
            finally:
                browser.close()

    def test_patient_portal_navigation_and_staff_denial(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                page.goto(self.live_server_url + "/portal/login/")
                page.get_by_label("Username").fill(self.portal_user.username)
                page.get_by_label("Password").fill(self.password)
                page.get_by_role("button", name="Sign in", exact=True).click()
                page.wait_for_url(self.live_server_url + "/portal/")
                expect(page.locator('nav a[aria-current="page"]')).to_have_text("Dashboard")
                expect(page.locator(".identity")).to_have_text(str(self.patient))
                for width in (1280, 390, 320):
                    page.set_viewport_size({"width": width, "height": 800})
                    self.no_overflow(page)
                    self.capture(page, f"patient-portal-{width}")
                response = page.goto(self.live_server_url + f"/app/patients/{self.patient.pk}/")
                self.assertEqual(response.status, 403)
                expect(page.locator("body")).not_to_contain_text(self.patient.mrn)
            finally:
                browser.close()
