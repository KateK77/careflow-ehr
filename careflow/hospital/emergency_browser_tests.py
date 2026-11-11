from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .test_emergency import EDFixture


class EmergencyBrowserTests(EDFixture, StaticLiveServerTestCase):
    def setUp(self):
        self.setup_ed()

    def test_arrival_triage_rooming_and_discharge(self):
        self.workflow(admit=False)

    def test_ed_to_inpatient_admission_and_bed_allocation(self):
        self.workflow(admit=True)

    def workflow(self, admit):
        from playwright.sync_api import expect, sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            ops, nurse, physician = [browser.new_page() for _ in range(3)]
            for page, actor in [(ops, self.operator), (nurse, self.nurse), (physician, self.physician)]:
                page.set_default_timeout(8000)
                page.goto(self.live_server_url + reverse("login"))
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(self.password)
                page.get_by_role("button", name="Sign in to workspace").click()

            ops.get_by_role("navigation", name="Main navigation").get_by_role("link", name="ED Tracking Board").click()
            ops.locator('select[name="patient"]').select_option(str(self.patient.pk))
            ops.locator('input[name="complaint"]').fill("Synthetic chief complaint")
            ops.get_by_label("Confirm synthetic ED registration").check()
            ops.get_by_role("button", name="Register arrival").click()
            path = ops.url

            def apply(page, action):
                page.locator('select[name="action"]').select_option(action)
                page.get_by_label("Confirm this fictional action").check()
                page.get_by_role("button", name="Apply ED action").click()

            nurse.goto(path)
            nurse.locator('select[name="category"]').select_option("demo_b")
            nurse.locator('textarea[name="note"]').fill("Synthetic triage")
            apply(nurse, "ed_triage")
            nurse.locator('select[name="room"]').select_option(str(self.ed_room.pk))
            nurse.locator('select[name="clinician"]').select_option(str(self.physician.pk))
            apply(nurse, "ed_room")
            physician.goto(path)
            apply(physician, "ed_provider")
            if admit:
                ops.reload()
                ops.locator('select[name="bed"]').select_option(str(self.bed.pk))
                ops.locator('textarea[name="note"]').fill("Synthetic admission disposition")
                apply(ops, "ed_admit")
                ops.get_by_role("link", name="Inpatient Stay #", exact=False).click()
                expect(ops.get_by_text("Bed 1", exact=False).first).to_be_visible()
            else:
                apply(physician, "ed_observation")
                physician.locator('textarea[name="note"]').fill("Synthetic discharge disposition")
                apply(physician, "ed_discharge")
                expect(physician.get_by_text("Disposition recorded", exact=False)).to_be_visible()
            browser.close()
