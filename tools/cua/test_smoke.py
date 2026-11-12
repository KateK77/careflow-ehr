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

from driver import BrowserDriver
from smoke import ROOT, native_run, qa_site, verify_login


class ComputerSmokeTests(unittest.TestCase):
    def test_sdk_continues_with_screenshot_and_same_browser(self):
        with tempfile.TemporaryDirectory(prefix="careflow-cua-test-") as temp:
            with qa_site(ROOT / ".venv/Scripts/python.exe", Path(temp)) as origin, sync_playwright() as playwright:
                browser = playwright.chromium.launch(timeout=10000)
                try:
                    context = browser.new_context(
                        viewport={"width": BrowserDriver.WIDTH, "height": BrowserDriver.HEIGHT},
                        device_scale_factor=1, service_workers="block", accept_downloads=False,
                    )
                    driver = BrowserDriver(context, origin, lambda: False)
                    toolset = ComputerToolset(driver)
                    initial = driver.screenshot()
                    bounds = driver.page.get_by_role("link", name="Staff Sign In", exact=True).bounding_box()
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
                                       "text": "Staff sign-in verified.", "annotations": []}]}]
                        return httpx.Response(200, json={
                            "id": f"resp_fixture_{len(requests)}", "created_at": 1, "model": "fixture-model",
                            "object": "response", "status": "completed", "output": output, "parallel_tool_calls": False,
                            "tool_choice": "auto", "tools": [{"type": "computer"}],
                        })

                    with OpenAI(api_key="offline-fixture", base_url="https://api.openai.com/v1", max_retries=0,
                                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
                        self.assertEqual(native_run(client, toolset, driver, "fixture-model", initial).status, "completed")
                    verify_login(driver)
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

    def test_native_mode_requires_explicit_approval(self):
        from argparse import Namespace
        from unittest.mock import patch

        from smoke import run

        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture"}):
            with self.assertRaisesRegex(ValueError, "explicit API approval"):
                run(Namespace(mode="native", approve_api_call=False, model="fixture-model"))


if __name__ == "__main__":
    unittest.main()
