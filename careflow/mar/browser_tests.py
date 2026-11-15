import secrets
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone

from .tests import MARFixture


class MARBrowserTests(MARFixture, StaticLiveServerTestCase):
    def test_nurse_records_from_workspace_and_physician_reads_history(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_pharmacy()
        receipt = self.dispense_order()
        # These browser inputs have whole-second precision. Do not truncate an
        # event into the fractional second before its just-created dispense.
        # Keep the service's lower bound intact; only allow test time to advance.
        time.sleep(1.05)
        nurse = self.staff["Nurse"]
        password = secrets.token_urlsafe(24)
        for actor in (nurse, self.physician):
            actor.set_password(password)
            actor.save()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 700, "height": 900})

            def login(actor):
                page.goto(self.live_server_url + "/login/")
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(password)
                page.get_by_role("button", name="Sign in to workspace").click()

            login(nurse)
            page.goto(self.live_server_url + reverse("nursing_workspace"))
            page.get_by_role("link", name="Open Medication Administration Record").click()
            page.get_by_role("link", name=f"Task {receipt.pk} · Synthetic Amber").click()
            page.get_by_role("link", name="Record simulated administration").click()
            page.locator("#id_occurred_at").fill(timezone.localtime().strftime("%Y-%m-%dT%H:%M:%S"))
            page.locator("#id_notes").fill("Fictional MAR browser note")
            page.locator("#id_confirmed").check()
            page.get_by_role("button", name="Record administration").click()
            expect(page.get_by_text("Effective MAR state: Administered")).to_be_visible()
            expect(page.get_by_text("Fictional MAR browser note")).to_be_visible()
            page.get_by_role("button", name="Sign out").click()
            login(self.physician)
            page.goto(self.live_server_url + reverse("mar_detail", args=[receipt.pk]))
            expect(page.get_by_text("Version 1 · Administered")).to_be_visible()
            expect(page.get_by_role("link", name="Record simulated administration")).to_have_count(0)
            browser.close()
