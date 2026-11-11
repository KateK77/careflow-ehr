from datetime import timedelta

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone

from .test_workflow import WorkflowFixture


class RadiologyBrowserTests(WorkflowFixture, StaticLiveServerTestCase):
    def test_radiology_publication_and_physician_review_after_encounter_completion(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_workflow()
        self.finish_encounter()
        order_path = reverse("imaging_report", args=[self.order.pk])
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            staff = browser.new_page()
            physician = browser.new_page(viewport={"width": 390, "height": 800})
            for page in (staff, physician):
                page.set_default_timeout(8000)

            def login(page, actor):
                page.goto(self.live_server_url + reverse("login"))
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(self.password)
                page.get_by_role("button", name="Sign in to workspace").click()

            def apply(action):
                staff.locator('select[name="action"]').select_option(action)
                staff.get_by_label("Confirm fictional radiology action").check()
                staff.get_by_role("button", name="Apply radiology action").click()

            login(staff, self.rad)
            staff.get_by_role("link", name=f"Order #{self.order.pk} · Synthetic X-ray").click()
            expect(staff.get_by_text(self.patient.mrn, exact=False)).to_have_count(0)
            apply("imaging_assign")
            expect(staff.get_by_text(self.patient.mrn, exact=False)).to_be_visible()
            slot = timezone.localtime(timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00")
            staff.locator('input[name="scheduled_at"]').fill(slot)
            apply("imaging_staff_schedule")
            apply("imaging_exam_start")
            staff.locator('input[name="study_id"]').fill("SYN-BROWSER-STUDY")
            staff.locator('input[name="body_site"]').fill("Synthetic region")
            apply("imaging_exam_perform")
            staff.locator('textarea[name="findings"]').fill("Synthetic browser findings")
            staff.locator('textarea[name="impression"]').fill("Synthetic browser impression")
            apply("imaging_report_draft")
            apply("imaging_preliminary")
            apply("imaging_exam_complete")
            apply("imaging_final")

            login(physician, self.physician)
            physician.goto(self.live_server_url + reverse("imaging_review_worklist"))
            physician.get_by_role("link", name="Synthetic X-ray", exact=False).click()
            expect(physician.get_by_text("Synthetic browser findings", exact=True)).to_be_visible()
            physician.get_by_label("Confirm review of this published revision").check()
            physician.get_by_role("button", name="Acknowledge report").click()
            expect(physician.get_by_text("Acknowledged by", exact=False)).to_be_visible()

            staff.reload()
            staff.locator('textarea[name="findings"]').fill("Synthetic corrected findings")
            staff.locator('input[name="reason"]').fill("Synthetic correction")
            apply("imaging_correct")
            physician.reload()
            expect(physician.get_by_text("Synthetic corrected findings", exact=True)).to_be_visible()
            expect(physician.get_by_role("button", name="Acknowledge report")).to_be_visible()

            staff.locator('select[name="withdrawal_kind"]').select_option("context_error")
            staff.locator('input[name="reason"]').fill("Synthetic context mismatch")
            apply("imaging_withdraw")
            expect(staff.get_by_text("Synthetic corrected findings", exact=True)).to_have_count(0)
            physician.goto(self.live_server_url + order_path)
            expect(physician.get_by_text("Report content is unavailable", exact=False)).to_be_visible()
            expect(physician.get_by_text("Synthetic corrected findings", exact=True)).to_have_count(0)
            browser.close()
