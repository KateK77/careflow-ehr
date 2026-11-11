from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .tests import HospitalFixture


class HospitalBrowserTests(HospitalFixture, StaticLiveServerTestCase):
    def test_admission_transfer_and_discharge(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_hospital()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            ops = browser.new_page()
            physician = browser.new_page(viewport={"width": 390, "height": 800})
            for page in (ops, physician):
                page.set_default_timeout(8000)

            def sign_in(page, actor):
                page.goto(self.live_server_url + reverse("login"))
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(self.password)
                page.get_by_role("button", name="Sign in to workspace").click()

            sign_in(ops, self.operator)
            ops.get_by_role("link", name="Admission worklist").click()
            ops.locator('select[name="patient"]').select_option(str(self.patient.pk))
            ops.locator('input[name="reason"]').fill("Synthetic admission")
            ops.get_by_role("button", name="Create admission request").click()
            ops.locator('select[name="bed"]').select_option(str(self.bed.pk))
            ops.locator('select[name="attending"]').select_option(str(self.physician.pk))
            ops.get_by_label("Confirm this fictional action").check()
            ops.get_by_role("button", name="Apply admission decision").click()
            ops.get_by_role("link", name="Stay #", exact=False).click()
            stay_url = ops.url

            def apply(page, action, note):
                page.locator('select[name="action"]').select_option(action)
                page.locator('textarea[name="note"]').fill(note)
                page.get_by_label("Confirm this fictional action").check()
                page.get_by_role("button", name="Apply stay action").click()

            ops.locator('select[name="bed"]').select_option(str(self.destination.pk))
            apply(ops, "hospital_transfer", "Synthetic transfer")
            expect(ops.get_by_text("Synthetic transfer", exact=False)).to_be_visible()
            sign_in(physician, self.physician)
            physician.goto(stay_url)
            apply(physician, "hospital_discharge_plan", "Synthetic discharge plan")
            ops.reload()
            apply(ops, "hospital_discharge", "Synthetic discharge summary")
            expect(ops.get_by_role("heading", name="Discharge documentation")).to_be_visible()
            ops.get_by_role("link", name="Bed capacity").click()
            expect(ops.get_by_text("2 available of 2 configured beds.")).to_be_visible()
            browser.close()
