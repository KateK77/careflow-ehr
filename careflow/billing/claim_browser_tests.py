from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .test_claims import ClaimFixture


class ClaimBrowserTests(ClaimFixture, StaticLiveServerTestCase):
    def test_claim_denial_appeal_payments_and_patient_summary(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_claims()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            staff = browser.new_page()
            patient = browser.new_page(viewport={"width": 390, "height": 800})
            staff.set_default_timeout(8000)
            patient.set_default_timeout(8000)

            def login(page, actor, password, route, button):
                page.goto(self.live_server_url + reverse(route))
                page.get_by_label("Username").fill(actor.username)
                page.get_by_label("Password").fill(password)
                page.get_by_role("button", name=button, exact=True).click()

            login(staff, self.biller, self.billing_password, "login", "Sign in to workspace")
            staff.get_by_role("link", name="Mock Claims", exact=True).click()
            staff.get_by_role("link", name=f"Create claim for statement #{self.statement.pk}").click()
            staff.get_by_label("Synthetic coverage revision").select_option(str(self.policy.pk))
            staff.get_by_label("Confirm fictional simulator action").check()
            staff.get_by_role("button", name="Save draft").click()

            def claim_action():
                staff.get_by_label("Confirm fictional simulator action").check()
                staff.get_by_role("button", name="Apply claim action").click()

            claim_action()
            claim_action()
            staff.locator('select[name="outcome"]').select_option("denied")
            staff.locator('input[name="payer_cents"]').fill("0")
            staff.locator('select[name="denial"]').select_option("demo_scope")
            claim_action()
            expect(staff.get_by_text("Synthetic plan scope", exact=True)).to_be_visible()

            def appeal_action(action):
                staff.locator('select[name="action"]').select_option(action)
                staff.get_by_label("Confirm fictional simulator action").check()
                staff.get_by_role("button", name="Apply appeal action").click()

            staff.locator('textarea[name="explanation"]').fill("Synthetic appeal")
            appeal_action("billing_appeal_save")
            appeal_action("billing_appeal_submit")
            staff.get_by_label("Review explanation").fill("Synthetic reconsideration")
            staff.locator('select[name="outcome"]').select_option("partial")
            staff.locator('input[name="payer_cents"]').fill("2000")
            appeal_action("billing_appeal_overturn")
            expect(staff.get_by_role("heading", name="Appeal #", exact=False)).to_contain_text("Denial overturned")

            staff.get_by_role("link", name=f"Encounter #{self.encounter.pk}", exact=False).click()
            staff.get_by_role("link", name="Simulated payments").click()
            for source, cents in [("patient", "1765"), ("payer", "2000")]:
                staff.locator('select[name="source"]').select_option(source)
                staff.get_by_label("Payment in cents").fill(cents)
                staff.get_by_label("Fictional transaction reference").fill(f"SYN-{source.upper()}")
                staff.get_by_label("Confirm this simulated transaction").check()
                staff.get_by_role("button", name="Record simulated transaction").click()
            expect(staff.get_by_text("Total $37.65 · Paid", exact=True)).to_be_visible()

            login(patient, self.portal_a, self.password, "portal_login", "Sign in")
            patient.get_by_role("link", name="Billing", exact=True).click()
            patient.get_by_role("link", name=f"Statement #{self.statement.pk}").click()
            patient.get_by_role("link", name="Simulated payment history").click()
            expect(patient.get_by_text("Total $37.65 · Paid", exact=True)).to_be_visible()
            expect(patient.get_by_text("SYN-PAYER", exact=True)).to_have_count(0)
            browser.close()
