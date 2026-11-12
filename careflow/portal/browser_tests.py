from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .tests import PortalFixture


class PortalBrowserTests(PortalFixture, StaticLiveServerTestCase):
    def test_patient_navigation_released_results_and_isolation(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_portal()
        self.release()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 390, "height": 800})

            def login(actor):
                page.goto(self.live_server_url + reverse("portal_login"))
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(self.password)
                page.get_by_role("button", name="Sign in", exact=True).click()

            login(self.portal_a)
            expect(page.get_by_role("heading", name="Patient dashboard")).to_be_visible()
            page.get_by_role("link", name="Laboratory results", exact=True).click()
            expect(page.get_by_role("rowheader", name="SYN-A")).to_be_visible()
            page.get_by_role("link", name="Appointments", exact=True).click()
            expect(page.get_by_role("heading", name="Appointment history")).to_be_visible()
            page.get_by_role("button", name="Sign out").click()
            login(self.portal_b)
            response = page.goto(self.live_server_url + reverse("portal_result", args=[self.original.pk]))
            self.assertEqual(response.status, 404)
            browser.close()
