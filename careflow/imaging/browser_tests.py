from datetime import timedelta

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone

from .tests import ImagingFixture


class ImagingBrowserTests(ImagingFixture, StaticLiveServerTestCase):
    def test_physician_orders_from_encounter_and_schedules(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_imaging()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.set_default_timeout(8000)
            page.goto(self.live_server_url + reverse("login"))
            page.get_by_label("Username").fill(self.physician.username)
            page.get_by_label("Password").fill(self.password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.goto(self.live_server_url + reverse("encounter_detail", args=[self.patient.pk, self.encounter.pk]))
            page.get_by_role("link", name="Create imaging order").click()
            page.locator('select[name="catalog"]').select_option(str(self.catalog_item.pk))
            page.locator('textarea[name="indication"]').fill("Fictional browser indication")

            def apply(action):
                page.locator('select[name="action"]').select_option(action)
                page.get_by_label("Confirm fictional imaging action").check()
                page.get_by_role("button", name="Apply action").click()

            apply("imaging_draft")
            apply("imaging_sign")
            slot = timezone.localtime(timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT10:00")
            page.locator('input[name="scheduled_at"]').fill(slot)
            apply("imaging_schedule")
            expect(page.get_by_text("Examination scheduled", exact=False).first).to_be_visible()
            page.goto(self.live_server_url + reverse("patient_chart", args=[self.patient.pk]))
            expect(page.get_by_role("link", name="Synthetic X-ray")).to_be_visible()
            browser.close()
