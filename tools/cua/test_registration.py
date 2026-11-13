"""Offline policy and real-browser rehearsal for the first writable UAT batch."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode

from openai import ComputerToolset
from openai.types.responses import ResponseComputerToolCall
from openai.types.responses.computer_action import Click, Type
from playwright.sync_api import sync_playwright

from diagnostics import Diagnostics
from driver import BrowserDriver
from registration import MAX_ACTIONS, MAX_REQUESTS, RegistrationPolicy, USERNAME, check_request_budget
from smoke import ROOT, local_environment, offline_rehearsal, qa_site, verify_login, write_capture
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
                driver = None
                try:
                    context = browser.new_context(viewport={"width": 1280, "height": 800}, service_workers="block")
                    driver = BrowserDriver(context, origin, lambda: False, max_actions=MAX_ACTIONS, policy=policy)
                    page = driver.page
                    toolset = ComputerToolset(driver)
                    evidence = Path(os.environ["CAREFLOW_CUA_OFFLINE_EVIDENCE"]) if "CAREFLOW_CUA_OFFLINE_EVIDENCE" in os.environ else None
                    if evidence is not None:
                        evidence.mkdir(parents=True, exist_ok=False)
                        driver.on_screenshot = lambda shot: write_capture(
                            evidence, f"screen-{driver.capture_count:02d}.png", shot,
                        )

                    def click_and_capture(locator):
                        locator.scroll_into_view_if_needed()
                        bounds = locator.bounding_box()
                        action = Click(type="click", button="left",
                                       x=int(bounds["x"] + bounds["width"] / 2),
                                       y=int(bounds["y"] + bounds["height"] / 2))
                        output = toolset.execute(ResponseComputerToolCall(
                            type="computer_call", id="cu_frontdesk", call_id="frontdesk",
                            status="completed", pending_safety_checks=[], actions=[action],
                        ), before_action=driver.before_action, cancelled=driver.cancelled)
                        self.assertEqual(output["output"]["type"], "computer_screenshot")

                    driver.screenshot()
                    offline_rehearsal(toolset, driver, "registration")
                    verify_login(driver, "registration")
                    driver.screenshot()
                    page.locator("[name=username]").fill(USERNAME)
                    page.locator("[name=password]").focus()
                    driver.type(Type(type="type", text="QA_PASSWORD"))
                    click_and_capture(page.get_by_role("button", name="Sign in to workspace"))
                    self.assertEqual(page.url, origin + "/app/dashboard/")
                    click_and_capture(page.get_by_role("link", name="Patients", exact=True))
                    click_and_capture(page.get_by_role("link", name="Register patient", exact=True))
                    for field, value in {"mrn": "SYN-CUA-001", "first_name": "Synthetic",
                                         "last_name": "Journey", "dob": "1990-01-15"}.items():
                        page.locator(f"[name={field}]").fill(value)
                    page.locator("[name=sex]").select_option("unknown")
                    page.locator("[name=synthetic_only]").check()
                    click_and_capture(page.get_by_role("button", name="Save patient"))
                    self.assertEqual(page.url, origin + "/app/patients/1/")
                    click_and_capture(page.get_by_role("link", name="Schedule", exact=True))
                    click_and_capture(page.get_by_role("link", name="New appointment", exact=True))
                    page.locator("[name=patient]").select_option("1")
                    page.locator("[name=physician]").select_option(str(fixture["physician"]))
                    page.locator("[name=start_at]").fill(fixture["start"])
                    click_and_capture(page.locator("button[value=review]"))
                    click_and_capture(page.locator("button[value=confirm]"))
                    self.assertEqual(page.url, origin + "/app/appointments/1/")
                    click_and_capture(page.get_by_role("button", name="Mark Arrived"))
                    self.assertTrue(page.locator(".state-arrived").is_visible())
                    self.assertTrue(page.get_by_role("heading", name="Appointment history").is_visible())
                    self.assertTrue(page.get_by_text("appointment_arrive", exact=True).is_visible())
                    self.assertEqual(policy.completed, ["sign_in", "register", "review", "confirm", "check_in"])
                    checks = verify(directory)
                    self.assertTrue(all(checks.values()))
                    if evidence is not None:
                        (evidence / "result.json").write_text(json.dumps({
                            "mode": "offline", "status": "pass", "requests_attempted": 0,
                            "actions_requested": driver.actions, "checkpoints": policy.completed,
                            "checks": checks, "screenshots": driver.capture_count,
                        }, indent=2), encoding="utf8")
                finally:
                    try:
                        if driver is not None:
                            driver.close()
                    finally:
                        browser.close()


if __name__ == "__main__":
    unittest.main()
