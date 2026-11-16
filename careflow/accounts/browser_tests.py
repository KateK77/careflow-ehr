"""Offline Chromium registration and approval; no email or paid API calls."""
import os
import secrets
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from careflow.portal.models import PatientPortalAccount
from .models import Enrollment


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccountBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(24)
        self.admin = get_user_model().objects.create_user("v3-operator", password=self.password)
        self.admin.groups.add(Group.objects.get_or_create(name="Administrator")[0])

    def page(self, browser):
        page = browser.new_page(viewport={"width": 1280, "height": 900}, service_workers="block")
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(self.live_server_url + "/") else route.abort())
        page.set_default_timeout(10000)
        return page

    def signup(self, page, kind, username):
        page.goto(self.live_server_url + f"/accounts/register/{kind}/")
        page.get_by_label("Username", exact=True).fill(username)
        page.get_by_label("Password", exact=True).fill(self.password)
        page.get_by_label("Confirm password", exact=True).fill(self.password)
        if kind == "staff":
            page.get_by_label("Requested staff role").select_option("Nurse")
        page.get_by_label("I will use only fictional patient information").check()
        page.get_by_role("button", name="Create patient account" if kind == "patient" else "Submit staff application").click()
        page.wait_for_url(f"**/accounts/complete/{kind}/")

    def login(self, page, username, patient=False):
        page.goto(self.live_server_url + ("/portal/login/" if patient else "/login/"))
        page.get_by_label("Username").fill(username)
        page.get_by_label("Password").fill(self.password)
        page.get_by_role("button", name="Sign in" if patient else "Sign in to workspace", exact=True).click()

    def capture(self, page, name):
        directory = os.environ.get("CAREFLOW_V3_SCREENSHOTS")
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(directory) / (name + ".png")), full_page=True)

    def test_patient_username_registration_login_and_isolation(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                self.signup(page, "patient", "browser.patient")
                expect(page.get_by_role("heading", name="Patient account created")).to_be_visible()
                self.capture(page, "patient-created")
                self.login(page, "browser.patient", patient=True)
                page.wait_for_url("**/portal/")
                expect(page.get_by_role("heading", name="Patient dashboard")).to_be_visible()
                self.assertEqual(page.goto(self.live_server_url + "/app/accounts/applications/").status, 403)
                page.goto(self.live_server_url + "/portal/")
                page.get_by_role("button", name="Sign out").click()
                self.login(page, "browser.patient", patient=True)
                page.wait_for_url("**/portal/")
            finally:
                browser.close()
        item = Enrollment.objects.get(user__username="browser.patient")
        self.assertTrue(item.user.check_password(self.password))
        self.assertEqual(PatientPortalAccount.objects.filter(user=item.user).count(), 1)
        self.assertEqual(item.events.get().action, "registration")

    def test_staff_application_approval_and_role_boundary(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                self.signup(page, "staff", "browser.nurse")
                expect(page.get_by_role("heading", name="Staff application submitted")).to_be_visible()
                self.capture(page, "staff-awaiting-review")
                self.login(page, "browser.nurse")
                expect(page.locator("form .errorlist")).to_be_visible()
                admin = self.page(browser)
                self.login(admin, self.admin.username)
                admin.wait_for_url("**/app/dashboard/")
                admin.get_by_role("link", name="Staff applications").click()
                admin.get_by_role("link", name="Review application").click()
                admin.get_by_label("Decision", exact=True).select_option("approve")
                admin.get_by_label("Role", exact=True).select_option("Nurse")
                admin.get_by_label("Reason", exact=True).fill("Approved synthetic browser applicant.")
                admin.get_by_role("button", name="Save review decision").click()
                admin.wait_for_url("**/app/accounts/applications/")
                self.login(page, "browser.nurse")
                page.wait_for_url("**/app/dashboard/")
                self.assertEqual(page.goto(self.live_server_url + "/app/patients/new/").status, 403)
            finally:
                browser.close()
        item = Enrollment.objects.get(user__username="browser.nurse")
        self.assertEqual(item.status, "approved")
        self.assertEqual(list(item.user.groups.values_list("name", flat=True)), ["Nurse"])
        self.assertEqual(item.events.filter(action="staff_approved").count(), 1)

    def test_blue_theme_registration_links_and_mobile_form(self):
        from playwright.sync_api import expect, sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = self.page(browser)
                page.goto(self.live_server_url)
                self.assertEqual(page.locator("a.landing-action").first.evaluate("el => getComputedStyle(el).backgroundColor"), "rgb(36, 93, 168)")
                expect(page.get_by_role("link", name="Create patient account")).to_be_visible()
                expect(page.get_by_role("link", name="Apply for staff access")).to_be_visible()
                self.capture(page, "v3-home-desktop")
                page.get_by_role("link", name="Create patient account").click()
                expect(page.get_by_label("Username", exact=True)).to_have_attribute("autocomplete", "username")
                self.assertEqual(page.locator('input[type="email"]').count(), 0)
                expect(page.get_by_label("I will use only fictional patient information")).not_to_be_checked()
                self.capture(page, "v3-patient-registration-desktop")
                for width in (390, 320):
                    page.set_viewport_size({"width": width, "height": 844})
                    page.wait_for_load_state("load")
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width)
                    self.capture(page, f"v3-registration-{width}")
            finally:
                browser.close()
