"""Exercise screenshot readiness and route disposal without databases or API calls."""
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from openai.types.responses.computer_action import Click
from playwright.sync_api import Error, Route, sync_playwright

from driver import BrowserDriver
from smoke import local_environment


class BrowserLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.started = threading.Event()
        self.release = threading.Event()
        started, release = self.started, self.release

        class Fixture(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                if self.path == "/static/slow.svg":
                    started.set()
                    release.wait(5)
                    body = b'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12"/>'
                    content_type = "image/svg+xml"
                else:
                    body = {
                        "/": b'<a href="/login/">Staff Sign In</a>',
                        "/login/": b'<h1>Staff sign in</h1><img src="/static/slow.svg">',
                    }[self.path]
                    content_type = "text/html"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                try:
                    self.wfile.write(body)
                except ConnectionError:
                    # The teardown-race fixture deliberately closes an outstanding connection.
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(worker.join)
        self.addCleanup(server.shutdown)
        self.addCleanup(self.release.set)
        self.origin = f"http://127.0.0.1:{server.server_port}"
        playwright = sync_playwright().start()
        self.addCleanup(playwright.stop)
        browser = playwright.chromium.launch(timeout=10000, env=local_environment())
        self.addCleanup(browser.close)
        self.context = browser.new_context(service_workers="block")
        self.driver = BrowserDriver(self.context, self.origin, lambda: False)
        self.addCleanup(self.driver.close)

    def navigate(self):
        bounds = self.driver.page.get_by_role("link", name="Staff Sign In").bounding_box()
        self.driver.click(Click(type="click", button="left", x=int(bounds["x"] + 4), y=int(bounds["y"] + 4)))

    def test_screenshot_after_click_waits_for_delayed_resource(self):
        self.navigate()
        self.driver.page.wait_for_url(self.origin + "/login/", wait_until="domcontentloaded")
        timer = threading.Timer(0.8, self.release.set)
        timer.start()
        try:
            self.assertEqual(self.driver.screenshot()["type"], "computer_screenshot")
            self.assertTrue(self.started.is_set())
            self.assertEqual(self.driver.page.locator("img").evaluate("(img) => img.naturalWidth"), 12)
        finally:
            timer.cancel()
            timer.join()

    def test_cleanup_drains_pending_route_before_context_disposal(self):
        self.navigate()
        self.driver.page.wait_for_url(self.origin + "/login/", wait_until="domcontentloaded")
        self.driver.page.wait_for_function("() => document.querySelector('img') !== null")
        self.assertTrue(self.started.wait(1))
        self.assertFalse(self.release.is_set())
        timer = threading.Timer(0.4, self.release.set)
        timer.start()
        try:
            self.driver.close()
            self.assertTrue(self.release.is_set())
            self.assertIsNone(self.driver.route_error)
        finally:
            timer.cancel()
            timer.join()

    def test_route_disposal_error_during_active_screenshot_is_reported(self):
        fetch = Route.fetch

        def fail_static_fetch(route, **kwargs):
            if route.request.url.endswith("/static/slow.svg"):
                raise Error("Route.fetch: Request context disposed")
            return fetch(route, **kwargs)

        with patch.object(Route, "fetch", fail_static_fetch):
            self.navigate()
            with self.assertRaisesRegex(Error, "Request context disposed"):
                self.driver.screenshot()
