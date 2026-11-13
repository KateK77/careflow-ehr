"""Verify bounded navigation recovery without retrying browser failures."""
import unittest
from unittest.mock import Mock

from playwright.sync_api import Error

from diagnostics import CAPTURE_DOCUMENT_REPLACED
from driver import BrowserDriver


class CaptureRetryTests(unittest.TestCase):
    def setUp(self):
        self.driver = BrowserDriver(Mock(), "http://127.0.0.1:1", lambda: False)
        self.driver.page.url = self.driver.origin + "/"
        self.driver.page.is_closed.return_value = False

    def test_replaced_document_retries_capture(self):
        capture = self.driver.page.screenshot
        capture.side_effect = [Error(CAPTURE_DOCUMENT_REPLACED), b"png"]
        self.assertEqual(self.driver.screenshot()["image_url"], "data:image/png;base64,cG5n")
        self.assertEqual(capture.call_count, 2)

    def test_replaced_document_retries_are_bounded(self):
        capture = self.driver.page.screenshot
        capture.side_effect = Error(CAPTURE_DOCUMENT_REPLACED)
        with self.assertRaisesRegex(Error, "Execution context was destroyed"):
            self.driver.screenshot()
        self.assertEqual(capture.call_count, 3)

    def test_failed_capture_preserves_only_allowlisted_page_state(self):
        self.driver.page.screenshot.side_effect = Error("Page.screenshot: Protocol error (private detail)")
        with self.assertRaises(Error):
            self.driver.screenshot()
        self.assertEqual(self.driver.capture_state, {
            "path": "/", "attempt": 1, "load_wait_completed": True,
            "routes_in_flight": 0, "page_closed": False,
        })
        self.assertIsNone(self.driver._capture_path(self.driver.origin + "/login/?private=secret"))
        self.assertIsNone(self.driver._capture_path("https://example.com/"))

    def test_pending_navigation_retries_without_replaying_actions(self):
        capture = self.driver.page.screenshot
        capture.side_effect = [Error("Page.screenshot: Frame is currently attempting a navigation"), b"png"]
        self.assertEqual(self.driver.screenshot()["image_url"], "data:image/png;base64,cG5n")
        self.assertEqual(capture.call_count, 2)
        self.assertEqual(self.driver.actions, [])

    def test_unrelated_capture_error_is_not_retried(self):
        capture = self.driver.page.screenshot
        capture.side_effect = Error("Browser target closed")
        with self.assertRaisesRegex(Error, "Browser target closed"):
            self.driver.screenshot()
        capture.assert_called_once()
