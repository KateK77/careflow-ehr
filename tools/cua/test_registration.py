"""Offline policy and real-browser rehearsal for the first writable UAT batch."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode

from openai import ComputerToolset
from openai.types.responses import ResponseComputerToolCall
from openai.types.responses.computer_action import Click, Keypress, Type
from playwright.sync_api import sync_playwright

from diagnostics import Diagnostics
from driver import BrowserDriver
from registration import MAX_ACTIONS, MAX_REQUESTS, RegistrationPolicy, USERNAME, check_request_budget
from smoke import ROOT, local_environment, offline_rehearsal, qa_site, verify_login, verify_registration_workflow, write_capture


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

    def test_registration_only_offline(self):
        self.rehearse("registration-only")

    def test_appointment_only_offline(self):
        self.rehearse("appointment-only")

    def test_checkin_only_offline(self):
        self.rehearse("checkin-only")

    def test_real_forms_and_audit_checkpoints_offline(self):
        self.rehearse("registration")

    def rehearse(self, scenario):
        with tempfile.TemporaryDirectory(prefix="careflow-registration-test-") as temporary:
            directory = Path(temporary)
            with qa_site(ROOT / ".venv/Scripts/python.exe", directory, scenario) as origin, sync_playwright() as pw:
                fixture = json.loads((directory / "fixture.json").read_text(encoding="utf8"))
                policy = RegistrationPolicy(fixture, scenario)
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
                    offline_rehearsal(toolset, driver, scenario)
                    verify_login(driver, scenario)
                    driver.screenshot()
                    page.locator("[name=username]").fill(USERNAME)
                    page.locator("[name=password]").focus()
                    driver.type(Type(type="type", text="QA_PASSWORD"))
                    click_and_capture(page.get_by_role("button", name="Sign in to workspace"))
                    self.assertEqual(page.url, origin + "/app/dashboard/")
                    if scenario in {"registration", "registration-only"}:
                        click_and_capture(page.get_by_role("link", name="Patients", exact=True))
                        click_and_capture(page.get_by_role("link", name="Register patient", exact=True))
                        page.locator("[name=email]").focus()
                        with self.assertRaisesRegex(ValueError, "Focus the designated"):
                            driver.type(Type(type="type", text="1990-01-15"))
                        self.assertEqual(page.locator("[name=email]").input_value(), "")
                        page.locator("[name=email]").fill("1990-01-15")
                        click_and_capture(page.get_by_role("button", name="Save patient"))
                        incomplete = Diagnostics()
                        with self.assertRaisesRegex(RuntimeError, "stopped before all expected"):
                            verify_registration_workflow(driver, directory, incomplete)
                        self.assertEqual(incomplete.stage, "registration_checkpoints")
                        self.assertEqual(incomplete.checks["final_path"], "/app/patients/new/")
                        self.assertTrue(incomplete.checks["registration_form_invalid"])
                        self.assertIn({"field": "sex", "flags": ["valueMissing"]},
                                      incomplete.checks["invalid_fields"])
                        self.assertIn({"field": "synthetic_only", "flags": ["valueMissing"]},
                                      incomplete.checks["invalid_fields"])
                        self.assertNotIn("1990-01-15", str(incomplete.checks))
                        self.assertEqual(policy.completed, ["sign_in"])
                        page.locator("[name=email]").clear()
                        for field, value in {"mrn": "SYN-CUA-001", "first_name": "Synthetic",
                                             "last_name": "Journey"}.items():
                            page.locator(f"[name={field}]").fill(value)
                        page.locator("[name=dob]").focus()
                        driver.type(Type(type="type", text="1990-01-15"))
                        sex = page.get_by_role("group", name="Recorded sex (required)")
                        unknown = sex.get_by_role("radio", name="Unknown")
                        self.assertEqual(sex.locator("input:checked").count(), 0)
                        self.assertTrue(unknown.is_visible())
                        self.assertIn("id_sex_helptext", sex.get_attribute("aria-describedby"))
                        sex.get_by_role("radio").first.focus()
                        driver.keypress(Keypress(type="keypress", keys=["ARROWLEFT"]))
                        self.assertTrue(unknown.is_checked())
                        confirmation = page.get_by_role("group", name="Required before saving").get_by_role(
                            "checkbox", name="I confirm this record contains synthetic data only. (required)",
                        )
                        self.assertFalse(confirmation.is_checked())
                        self.assertTrue(confirmation.is_enabled())
                        if scenario == "registration-only":
                            click_and_capture(confirmation)
                            self.assertTrue(confirmation.is_checked())
                            click_and_capture(page.locator("label.registration-confirmation"))
                            self.assertFalse(confirmation.is_checked())
                            click_and_capture(page.get_by_role("button", name="Save patient"))
                            self.assertEqual(policy.completed, ["sign_in"])
                            self.assertEqual(confirmation.evaluate("(input) => input.validity.valueMissing"), True)
                        confirmation.focus()
                        driver.keypress(Keypress(type="keypress", keys=["SPACE"]))
                        self.assertTrue(confirmation.is_checked())
                        self.assertEqual(page.locator("[name=confirm_duplicate]").count(), 0)
                        click_and_capture(page.get_by_role("button", name="Save patient"))
                        self.assertEqual(page.url, origin + "/app/patients/1/")
                    if scenario in {"registration", "appointment-only"}:
                        click_and_capture(page.get_by_role("link", name="Schedule", exact=True))
                        click_and_capture(page.get_by_role("link", name="New appointment", exact=True))
                        if scenario == "appointment-only":
                            click_and_capture(page.locator("button[value=review]"))
                            incomplete = Diagnostics()
                            with self.assertRaisesRegex(RuntimeError, "stopped before all expected"):
                                verify_registration_workflow(driver, directory, incomplete)
                            self.assertEqual(incomplete.stage, "appointment_checkpoints")
                            self.assertEqual(incomplete.checks, {
                                "final_path": "/app/appointments/new/",
                                "appointment_form": {
                                    "invalid_fields": [
                                        {"field": field, "flags": ["valueMissing"]}
                                        for field in ("patient", "physician", "start_at")
                                    ],
                                    "server_errors_visible": False,
                                },
                                "appointment_count": 0,
                                "appointment_creation_audit_count": 0,
                            })
                            self.assertEqual(policy.completed, ["sign_in"])
                        page.locator("[name=patient]").select_option("1")
                        page.locator("[name=physician]").select_option(str(fixture["physician"]))
                        page.locator("[name=start_at]").focus()
                        driver.type(Type(type="type", text=fixture["start"]))
                        click_and_capture(page.locator("button[value=review]"))
                        click_and_capture(page.locator("button[value=confirm]"))
                        self.assertEqual(page.url, origin + "/app/appointments/1/")
                    if scenario in {"registration", "checkin-only"}:
                        if scenario == "checkin-only":
                            click_and_capture(page.get_by_role("link", name="Patient check-in", exact=True))
                            click_and_capture(page.locator('main a[href="/app/appointments/1/"]').first)
                        click_and_capture(page.get_by_role("button", name="Mark Arrived"))
                        self.assertTrue(page.locator(".state-arrived").is_visible())
                        self.assertTrue(page.get_by_role("heading", name="Appointment history").is_visible())
                        self.assertTrue(page.get_by_text("appointment_arrive", exact=True).is_visible())
                    self.assertEqual(tuple(policy.completed), policy.phases)
                    completed = Diagnostics()
                    verify_registration_workflow(driver, directory, completed)
                    checks = completed.checks
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
