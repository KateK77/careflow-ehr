import secrets

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .test_pharmacy import PharmacyFixture


class PharmacyBrowserTests(PharmacyFixture, StaticLiveServerTestCase):
    def test_claim_clarification_response_verification_and_simulated_dispensing(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_pharmacy()
        self.finish_encounter()
        password = secrets.token_urlsafe(24)
        for actor in (self.physician, self.pharmacist):
            actor.set_password(password)
            actor.save()
        pharmacy_detail = reverse("pharmacy_detail", args=[self.signed.public_id])
        physician_detail = reverse("med_detail", args=[self.signed.public_id])
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 700, "height": 900})

            def login(actor):
                page.goto(self.live_server_url + "/login/")
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(password)
                page.get_by_role("button", name="Sign in to workspace").click()

            def action(label, reason=None, quantity=None):
                page.get_by_role("link", name=label, exact=True).click()
                if reason:
                    page.locator("#id_reason").fill(reason)
                if quantity is not None:
                    page.locator("#id_quantity").fill(str(quantity))
                page.locator("#id_confirmed").check()
                page.get_by_role("button", name=label, exact=True).click()

            login(self.pharmacist)
            expect(page.get_by_role("heading", name="Pharmacy Workspace")).to_be_visible()
            expect(page.get_by_role("table", name="Unclaimed signed requisitions")).not_to_contain_text(self.patient.mrn)
            action("Claim order")
            expect(page.get_by_role("heading", name="Pharmacy Verification")).to_be_visible()
            expect(page.get_by_text("Completed", exact=False).first).to_be_visible()
            action("Request clarification", reason="Please confirm fictional instructions")
            expect(page.get_by_text("Clarification requested", exact=True).first).to_be_visible()

            page.get_by_role("button", name="Sign out").click()
            login(self.physician)
            page.goto(self.live_server_url + physician_detail)
            page.get_by_role("link", name="Respond to clarification").click()
            page.locator("#id_reason").fill("Follow the signed fictional instructions")
            page.locator("#id_confirmed").check()
            page.get_by_role("button", name="Submit response").click()
            expect(page.get_by_text("Awaiting verification", exact=True)).to_be_visible()

            page.get_by_role("button", name="Sign out").click()
            login(self.pharmacist)
            page.goto(self.live_server_url + pharmacy_detail)
            action("Approve verification")
            action("Record simulated dispensing", quantity=self.signed.quantity)
            expect(page.get_by_text("Simulated dispensing recorded: 2 units", exact=False)).to_be_visible()
            expect(page.get_by_role("link", name="Record simulated dispensing")).to_have_count(0)
            expect(page.get_by_role("link", name="Patients", exact=True)).to_have_count(0)
            browser.close()
