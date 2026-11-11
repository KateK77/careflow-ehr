from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .tests import BillingFixture


class BillingBrowserTests(BillingFixture, StaticLiveServerTestCase):
    def test_staff_charge_release_and_patient_visibility(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_billing()
        self.finish_encounter()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            staff = browser.new_page()
            patient = browser.new_page(viewport={"width": 390, "height": 800})
            staff.set_default_timeout(7000)
            patient.set_default_timeout(7000)
            staff.goto(self.live_server_url + reverse("login"))
            staff.get_by_label("Username").fill(self.biller.username)
            staff.get_by_label("Password").fill(self.billing_password)
            staff.get_by_role("button", name="Sign in to workspace").click()
            staff.get_by_role("link", name=f"Encounter #{self.encounter.pk}", exact=True).click()
            staff.get_by_label("Catalog").select_option(str(self.catalog_item.pk))
            staff.get_by_label("Quantity").fill("3")

            def apply(action):
                staff.locator('select[name="action"]').select_option(action)
                staff.get_by_label("Confirm this fictional billing action").check()
                staff.get_by_role("button", name="Apply action").click()

            apply("billing_charge_add")
            apply("billing_finalize")
            apply("billing_release")
            expect(staff.get_by_text("Statement released", exact=False)).to_be_visible()

            patient.goto(self.live_server_url + reverse("portal_login"))
            patient.get_by_label("Username").fill(self.portal_a.username)
            patient.get_by_label("Password").fill(self.password)
            patient.get_by_role("button", name="Sign in", exact=True).click()
            patient.get_by_role("link", name="Billing", exact=True).click()
            patient.get_by_role("link", name="Statement #").click()
            expect(patient.get_by_text("Synthetic visit charge", exact=True)).to_be_visible()
            expect(patient.get_by_text("Simulated balance $37.65", exact=False)).to_be_visible()
            browser.close()
