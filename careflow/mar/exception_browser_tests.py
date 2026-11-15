import secrets
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone

from .tests import MARFixture


class MARExceptionBrowserTests(MARFixture, StaticLiveServerTestCase):
    def test_hold_resolution_and_explicit_correction(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_pharmacy()
        receipt = self.dispense_order()
        # These browser inputs have whole-second precision. Do not truncate an
        # event into the fractional second before its just-created dispense.
        # Keep the service's lower bound intact; only allow test time to advance.
        time.sleep(1.05)
        nurse = self.staff["Nurse"]
        password = secrets.token_urlsafe(24)
        nurse.set_password(password)
        nurse.save()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 700, "height": 900})
            page.goto(self.live_server_url + "/login/")
            page.get_by_label("Username").fill(nurse.username)
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.goto(self.live_server_url + reverse("mar_detail", args=[receipt.pk]))

            def submit(label):
                page.locator("#id_occurred_at").fill(timezone.localtime().strftime("%Y-%m-%dT%H:%M:%S"))
                page.locator("#id_confirmed").check()
                page.get_by_role("button", name=label, exact=True).click()

            page.get_by_role("link", name="Record MAR exception").click()
            page.locator("#id_status").select_option("held")
            page.locator("#id_reason").fill("Fictional hold")
            submit("Record exception")
            expect(page.get_by_text("Version 1 · Held")).to_be_visible()
            page.get_by_role("link", name="Record simulated administration").click()
            submit("Record administration")
            expect(page.get_by_text("Version 2 · Administered")).to_be_visible()
            page.get_by_role("link", name="Correct MAR documentation").click()
            page.locator("#id_status").select_option("omitted")
            page.locator("#id_quantity").fill("")
            page.locator("#id_reason").fill("Fictional omission")
            page.locator("#id_correction_reason").fill("Correct an inaccurate fictional entry")
            submit("Record correction")
            expect(page.get_by_text("Version 3 · Omitted / Not given")).to_be_visible()
            expect(page.get_by_text("Version 2 · Administered")).to_be_visible()
            expect(page.get_by_text("Superseded record", exact=True)).to_have_count(2)
            browser.close()
