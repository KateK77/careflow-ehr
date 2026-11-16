"""Exercise the SDK wire loop and browser policy without external API access."""
import base64
import json
import os
import tempfile
import unittest
from pathlib import Path

import httpx2 as httpx
from openai import ComputerToolset, OpenAI
from openai.types.responses import ResponseComputerToolCall
from openai.types.responses.computer_action import Click, Keypress, Scroll, Type
from playwright.sync_api import sync_playwright

from diagnostics import Diagnostics, safe_exception_chain
from driver import BrowserDriver
from smoke import ROOT, native_run, qa_site, verify_login


class ComputerSmokeTests(unittest.TestCase):
    def test_exception_chain_keeps_only_safe_browser_signature(self):
        from playwright.sync_api import Error

        try:
            try:
                raise Error("Page.screenshot: Execution context was destroyed, most likely because of a navigation"
                            "\nCookie: synthetic-secret")
            except Error as cause:
                raise RuntimeError("Authorization: synthetic-secret") from cause
        except RuntimeError as error:
            self.assertEqual(safe_exception_chain(error), [
                {"class": "RuntimeError"},
                {"class": "Error", "signature": "capture_document_replaced"},
            ])

    def test_patient_sdk_continues_with_screenshot_and_same_browser(self):
        diagnostic = Diagnostics()
        with tempfile.TemporaryDirectory(prefix="careflow-cua-test-") as temp:
            with qa_site(Path(os.environ.get("CAREFLOW_DJANGO_PYTHON", ROOT / ".venv/Scripts/python.exe")), Path(temp)) as origin, sync_playwright() as playwright:
                browser = playwright.chromium.launch(timeout=10000)
                try:
                    context = browser.new_context(
                        viewport={"width": BrowserDriver.WIDTH, "height": BrowserDriver.HEIGHT},
                        device_scale_factor=1, service_workers="block", accept_downloads=False,
                    )
                    driver = BrowserDriver(context, origin, lambda: False)
                    toolset = ComputerToolset(driver)
                    initial = driver.screenshot()
                    bounds = driver.page.get_by_role("link", name="Patient Sign In", exact=True).bounding_box()
                    self.assertIsNotNone(bounds)
                    call = ResponseComputerToolCall(
                        type="computer_call", id="cu_fixture", call_id="call_fixture",
                        status="completed", pending_safety_checks=[], actions=[
                            Click(type="click", button="left", x=int(bounds["x"] + 10), y=int(bounds["y"] + 10)),
                        ],
                    )
                    requests = []

                    def respond(request):
                        data = json.loads(request.content)
                        requests.append(data)
                        self.assertEqual(str(request.url), "https://api.openai.com/v1/responses")
                        self.assertEqual(data["tools"], [{"type": "computer"}])
                        self.assertFalse(data["store"])
                        if len(requests) == 1:
                            self.assertIn("Patient Sign In", data["input"][0]["content"][0]["text"])
                            self.assertEqual(data["input"][0]["content"][1]["image_url"], initial["image_url"])
                            output = [call.model_dump(exclude_none=True)]
                        else:
                            self.assertEqual(len(requests), 2)
                            output_item = data["input"][-1]
                            self.assertEqual(output_item["type"], "computer_call_output")
                            self.assertEqual(output_item["call_id"], "call_fixture")
                            encoded = output_item["output"]["image_url"].split(",", 1)[1]
                            self.assertTrue(base64.b64decode(encoded).startswith(b"\x89PNG"))
                            self.assertNotEqual(output_item["output"]["image_url"], initial["image_url"])
                            output = [{"type": "message", "id": "msg_fixture", "role": "assistant",
                                       "status": "completed", "content": [{"type": "output_text",
                                       "text": "Patient sign-in verified.", "annotations": []}]}]
                        return httpx.Response(200, json={
                            "id": f"resp_fixture_{len(requests)}", "created_at": 1, "model": "fixture-model",
                            "object": "response", "status": "completed", "output": output, "parallel_tool_calls": False,
                            "tool_choice": "auto", "tools": [{"type": "computer"}],
                            "usage": {"input_tokens": 1200, "output_tokens": 100, "total_tokens": 1300},
                        })

                    with OpenAI(api_key="offline-fixture", base_url="https://api.openai.com/v1", max_retries=0,
                                http_client=httpx.Client(transport=httpx.MockTransport(respond),
                                    event_hooks={"request": [diagnostic.request_started],
                                                 "response": [diagnostic.response_received, diagnostic.capture_usage]})) as client:
                        self.assertEqual(native_run(client, toolset, driver, "fixture-model", initial, scenario="patient").status, "completed")
                    verify_login(driver, "patient")
                    self.assertEqual(diagnostic.usage_summary(True), {
                        "input_tokens": 2400, "output_tokens": 200, "responses_with_usage": 2,
                        "complete": True, "estimated_token_cost_usd": 0.009,
                    })
                    self.assertFalse(driver.allows("https://example.com/login/"))
                    self.assertFalse(driver.allows(origin + "/app/patients/"))
                    self.assertFalse(driver.allows(origin + "/login/?next=/app/"))
                    driver.scroll(Scroll(type="scroll", x=10, y=10, scroll_x=0, scroll_y=200))
                    driver.page.get_by_label("Username").focus()
                    driver.type(Type(type="type", text="Synthetic"))
                    driver.keypress(Keypress(type="keypress", keys=["Backspace"]))
                    self.assertEqual(driver.page.get_by_label("Username").input_value(), "Syntheti")
                    with self.assertRaises(ValueError):
                        driver.keypress(Keypress(type="keypress", keys=["CTRL", "L"]))
                    with self.assertRaises(ValueError):
                        driver.click(Click(type="click", button="left", x=-1, y=10))
                    driver.remaining = 0
                    self.assertFalse(driver.before_action(call.actions[0]))
                    driver.cancelled = lambda: True
                    with self.assertRaises(RuntimeError):
                        driver.screenshot()
                finally:
                    browser.close()

    def test_native_error_diagnostics_with_mock_transport(self):
        from unittest.mock import Mock

        cases = [
            (429, {"error": {"code": "insufficient_quota", "message": "PRIVATE RESPONSE"}},
             "responses_api", "insufficient_quota", "confirmed by HTTP response"),
            (400, {"error": {"code": "unsupported_value", "param": "tools[0].type",
                             "message": "PRIVATE RESPONSE"}}, "responses_api", "unsupported_value",
             "API rejected the model or tool configuration"),
            (200, {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
                   "output": []}, "responses_validation", "none", "max_output_tokens"),
            (200, {"status": "completed", "output": [{
                "type": "computer_call", "id": "cu_mock", "call_id": "call_mock", "status": "completed",
                "actions": [{"type": "screenshot"}], "pending_safety_checks": [
                    {"id": "check_mock", "code": "untrusted_content", "message": "PRIVATE RESPONSE"},
                ],
            }]}, "computer_approval", "none", "safety_check_refused"),
        ]
        for status, body, stage, code, hint in cases:
            with self.subTest(stage=stage):
                diagnostic = Diagnostics()
                payload = {"id": "resp_mock", "created_at": 1, "model": "fixture-model", "object": "response",
                           "parallel_tool_calls": False, "tool_choice": "auto", "tools": [{"type": "computer"}],
                           **body}
                driver = Mock(cancelled=Mock(return_value=False))
                toolset = ComputerToolset(driver)
                transport = httpx.Client(
                    transport=httpx.MockTransport(lambda _: httpx.Response(status, json=payload)),
                    event_hooks={"request": [diagnostic.request_started], "response": [diagnostic.response_received]},
                )
                with OpenAI(api_key="PRIVATE KEY", base_url="https://api.openai.com/v1",
                            http_client=transport, max_retries=0) as client:
                    with self.assertRaises(Exception) as failure:
                        native_run(client, toolset, driver, "fixture-model",
                                   {"image_url": "data:image/png;base64,PRIVATE_SCREENSHOT"},
                                   on_diagnostic=diagnostic.tool_event)
                report = diagnostic.failure(failure.exception)
                for expected in (stage, f"HTTP status: {status}", f"API code: {code}", hint,
                                 "confirmed by HTTP response"):
                    self.assertIn(expected, report)
                self.assertNotIn("PRIVATE", report)
                self.assertEqual(diagnostic.attempts, 1)
                driver.screenshot.assert_not_called()

    def test_unconfirmed_delivery_and_local_failure_are_distinguished(self):
        diagnostic = Diagnostics()
        self.assertIn("Request sent: no", diagnostic.failure(ValueError("PRIVATE")))
        diagnostic.request_started(None)
        report = diagnostic.failure(TimeoutError("PRIVATE"))
        self.assertIn("attempted; delivery unconfirmed", report)
        self.assertNotIn("PRIVATE", report)

    def test_native_mode_requires_explicit_approval(self):
        from argparse import Namespace
        from unittest.mock import patch

        from smoke import run

        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"}):
            with self.assertRaisesRegex(ValueError, "explicit API approval"):
                run(Namespace(mode="native", approve_api_call=False, model="fixture-model"))


if __name__ == "__main__":
    unittest.main()
