import secrets

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from .tests import MedicationFixture


class MedicationBrowserTests(MedicationFixture, StaticLiveServerTestCase):
    def test_catalog_composer_review_and_signed_history(self):
        from playwright.sync_api import expect, sync_playwright

        self.setup_medications()
        password = secrets.token_urlsafe(24)
        self.physician.set_password(password)
        self.physician.save()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 700, "height": 900})
            page.goto(self.live_server_url + "/login/")
            page.get_by_label("Username").fill(self.physician.username)
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in to workspace").click()
            page.get_by_role("link", name="Medication Catalog", exact=True).click()
            expect(page.get_by_role("table", name="Fictional medication revisions")).to_contain_text("Synthetic Amber")
            page.goto(self.live_server_url + reverse("med_create", args=[self.patient.pk, self.encounter.pk]))
            page.locator("#id_catalog").select_option(str(self.medication.pk))
            page.locator("#id_dose").fill("1 demo units")
            page.locator("#id_route").select_option("oral")
            page.locator("#id_frequency").select_option("daily")
            page.locator("#id_duration").fill("2")
            page.locator("#id_quantity").fill("2")
            page.locator("#id_instructions").fill("Fictional browser instructions")
            page.locator("#id_confirmed").check()
            page.get_by_role("button", name="Save draft").click()
            page.get_by_role("link", name="Review and Sign").click()
            expect(page.get_by_text("Fictional browser instructions", exact=True)).to_be_visible()
            page.locator("#id_confirmed").check()
            page.get_by_role("button", name="Sign synthetic order").click()
            expect(page.get_by_text("Signed by", exact=False)).to_be_visible()
            page.get_by_role("link", name="Medication orders", exact=True).click()
            expect(page.get_by_role("table", name="Orders within your access")).to_contain_text("Signed")
            browser.close()
