import os
import re
import secrets
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from careflow.patients.models import Patient
from careflow.scheduling.models import Appointment


class LandingBrowserTests(StaticLiveServerTestCase):
    def test_landing_styles_responsive_layout_and_sign_in_links(self):
        from playwright.sync_api import expect, sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 960})
            loaded_styles = set()
            page.on("response", lambda response: loaded_styles.add(response.url)
                    if response.ok and response.request.resource_type == "stylesheet" else None)
            page.goto(self.live_server_url)
            for path in ("v2.css",):
                self.assertIn(f"{self.live_server_url}/static/core/{path}", loaded_styles)
            expect(page.get_by_role("heading", name="CareFlow EHR")).to_be_visible()
            cards = page.locator(".landing-card")
            for width in (1440, 768, 390, 320):
                page.set_viewport_size({"width": width, "height": 960})
                self.assertEqual(page.evaluate("document.documentElement.scrollWidth"), width)
                first, second = (cards.nth(index).bounding_box() for index in (0, 1))
                if width > 672:
                    self.assertEqual(first["y"], second["y"])
                    self.assertGreater(second["x"], first["x"])
                else:
                    self.assertGreater(second["y"], first["y"] + first["height"])
                output = os.environ.get("CAREFLOW_LANDING_SCREENSHOT_DIR")
                if output and width in (1440, 390):
                    page.screenshot(path=str(Path(output) / f"careflow-landing-{width}.png"), full_page=True)
            for label, path in (("Staff Sign In", "/login/"), ("Patient Sign In", "/portal/login/")):
                page.goto(self.live_server_url)
                link = page.get_by_role("link", name=label)
                # The v2 landing adds a skip link before the two real portal entries.
                page.keyboard.press("Tab")
                expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
                page.keyboard.press("Tab")
                if path == "/portal/login/":
                    page.keyboard.press("Tab")
                expect(link).to_be_focused()
                page.keyboard.press("Enter")
                expect(page).to_have_url(self.live_server_url + path)
                expect(page.get_by_label("Username")).to_be_visible()
            browser.close()


class ClinicalUiBrowserTests(StaticLiveServerTestCase):
    def test_date_guidance_responsive_worklist_and_duplicate_submit_guard(self):
        from playwright.sync_api import expect, sync_playwright

        password = secrets.token_urlsafe(24)
        actor = get_user_model().objects.create_user(username='ui.browser', password=password)
        actor.groups.add(Group.objects.get_or_create(name='Administrator')[0])
        patient = Patient.objects.create(mrn='UI-SYNTHETIC', first_name='Synthetic' + 'X' * 71,
            last_name='Integration' + 'Y' * 69, dob=date(1980, 1, 1), sex='unknown')
        now = timezone.now()
        Appointment.objects.create(patient=patient, physician=actor, start_at=now, end_at=now + timedelta(minutes=30),
                                   appointment_type='Synthetic UI test')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.goto(self.live_server_url + '/login/')
            page.get_by_label('Username').fill(actor.username)
            page.get_by_label('Password').fill(password)
            page.get_by_role('button', name='Sign in to workspace').click()
            page.wait_for_url('**/app/dashboard/')
            page.goto(self.live_server_url + '/app/patients/new/')
            field = page.locator('#id_dob')
            field.evaluate("el => { el.value='12020-04-15'; el.dispatchEvent(new Event('input',{bubbles:true})); }")
            self.assertFalse(field.evaluate('el => el.checkValidity()'))
            self.assertIn('four-digit year', field.evaluate('el => el.validationMessage'))
            for value in ['0001-01-01', '1899-04-15', '2020-04-15']:
                field.fill(value)
                self.assertTrue(field.evaluate('el => el.checkValidity()'))
                expect(field).to_have_value(value)
            page.goto(self.live_server_url + '/app/physician/')
            expect(page.get_by_text(str(patient), exact=True)).to_be_visible()
            for width in [1440, 700, 390]:
                page.set_viewport_size({'width': width, 'height': 1000})
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), page.evaluate('window.innerWidth'))
                expect(page.get_by_text(str(patient), exact=True)).to_be_visible()
            expect(page.locator('.scroll-hint').first).to_be_visible()
            output = os.environ.get('CAREFLOW_BROWSER_SCREENSHOT_DIR')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(Path(output) / 'shared-ui-mobile.png'), full_page=True)
            calls = []
            page.on('request', lambda request: calls.append(request.url) if request.url.split('?')[0].endswith('/health/') else None)
            page.evaluate("""() => {
              const existing=document.querySelector('form'); existing.method='get'; existing.action='/health/';
              existing.requestSubmit(); existing.requestSubmit();
            }""")
            page.wait_for_url(re.compile(r'/health/(\?.*)?$'))
            self.assertEqual(len(calls), 1)
            browser.close()
