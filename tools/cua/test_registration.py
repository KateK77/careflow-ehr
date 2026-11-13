"""Offline policy and real-browser rehearsal for the first writable UAT batch."""
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode

from openai import ComputerToolset
from openai.types.responses.computer_action import Type
from playwright.sync_api import sync_playwright

from diagnostics import Diagnostics
from driver import BrowserDriver
from registration import MAX_REQUESTS, RegistrationPolicy, USERNAME, check_request_budget
from smoke import ROOT, local_environment, offline_rehearsal, qa_site, verify_login
from verify_registration import verify


class RegistrationTests(unittest.TestCase):
    def test_scope_and_order_reject_wrong_credentials_and_write_paths(self):
        policy = RegistrationPolicy({"password": "test-only", "physician": 2, "start": "2026-11-12T10:00"})
        credentials = {"username": USERNAME, "password": "test-only"}
        self.assertFalse(policy.allow_post("http://localhost/login/", urlencode({**credentials, "next": "/app/"})))
        self.assertFalse(policy.allow_post("http://localhost/app/patients/new/", urlencode(credentials)))
        self.assertTrue(policy.allow_post("http://localhost/login/", urlencode(credentials)))
        self.assertFalse(policy.allow_post("http://localhost/login/", urlencode(credentials)))
        policy.observe_post(302)
        self.assertFalse(policy.allow_post("http://localhost/login/", urlencode(credentials)))
        self.assertFalse(policy.allows_page("/app/patients/2/"))

    def test_budget_stops_on_missing_usage_threshold_and_request_limit(self):
        diagnostic = Diagnostics()
        check_request_budget(diagnostic)
        diagnostic.attempts = 1
        with self.assertRaisesRegex(RuntimeError, "missing usage"):
            check_request_budget(diagnostic)
        diagnostic.usage = [(1000, 100)]
        check_request_budget(diagnostic)
        diagnostic.usage = [(300000, 0)]
        with self.assertRaisesRegex(RuntimeError, "estimate"):
            check_request_budget(diagnostic)
        diagnostic.attempts = MAX_REQUESTS
        with self.assertRaisesRegex(RuntimeError, "request limit"):
            check_request_budget(diagnostic)

    def test_real_forms_and_audit_checkpoints_offline(self):
        with tempfile.TemporaryDirectory(prefix="careflow-registration-test-") as temporary:
            directory = Path(temporary)
            with qa_site(ROOT / ".venv/Scripts/python.exe", directory, "registration") as origin, sync_playwright() as pw:
                fixture = json.loads((directory / "fixture.json").read_text(encoding="utf8"))
                policy = RegistrationPolicy(fixture)
                browser = pw.chromium.launch(timeout=10000, env=local_environment())
                try:
                    context = browser.new_context(viewport={"width": 1280, "height": 800}, service_workers="block")
                    driver = BrowserDriver(context, origin, lambda: False, policy=policy)
                    page = driver.page
                    driver.screenshot()
                    offline_rehearsal(ComputerToolset(driver), driver, "registration")
                    verify_login(driver, "registration")
                    driver.screenshot()
                    page.locator("[name=username]").fill(USERNAME)
                    page.locator("[name=password]").focus()
                    driver.type(Type(type="type", text="QA_PASSWORD"))
                    page.get_by_role("button", name="Sign in to workspace").click()
                    driver.screenshot()
                    self.assertEqual(page.url, origin + "/app/dashboard/")
                    page.goto(origin + "/app/patients/new/")
                    for field, value in {"mrn": "SYN-CUA-001", "first_name": "Synthetic",
                                         "last_name": "Journey", "dob": "1990-01-15"}.items():
                        page.locator(f"[name={field}]").fill(value)
                    page.locator("[name=sex]").select_option("unknown")
                    page.locator("[name=synthetic_only]").check()
                    page.get_by_role("button", name="Save patient").click()
                    page.wait_for_url(origin + "/app/patients/1/")
                    page.goto(origin + "/app/appointments/new/")
                    page.locator("[name=patient]").select_option("1")
                    page.locator("[name=physician]").select_option(str(fixture["physician"]))
                    page.locator("[name=start_at]").fill(fixture["start"])
                    page.locator("button[value=review]").click()
                    page.locator("button[value=confirm]").click()
                    page.wait_for_url(origin + "/app/appointments/1/")
                    page.get_by_role("button", name="Mark Arrived").click()
                    page.locator(".state-arrived").wait_for(state="visible")
                    self.assertEqual(policy.completed, ["sign_in", "register", "review", "confirm", "check_in"])
                    self.assertTrue(all(verify(directory).values()))
                finally:
                    try:
                        driver.close()
                    finally:
                        browser.close()


if __name__ == "__main__":
    unittest.main()
