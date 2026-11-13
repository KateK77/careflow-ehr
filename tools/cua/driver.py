"""Browser-only implementation of the OpenAI native computer driver contract."""
import base64
import time
from urllib.parse import urljoin, urlsplit

from openai import ComputerDriver
from playwright.sync_api import BrowserContext, Error, Page

from diagnostics import CAPTURE_DOCUMENT_REPLACED, CAPTURE_NAVIGATION_PENDING, KeypressRejected


class BrowserDriver(ComputerDriver):
    """Keep native screenshot coordinates aligned to one fixed browser viewport."""

    WIDTH, HEIGHT = 1280, 800
    KEY_ALIASES = {
        "ARROWUP": "ArrowUp", "ARROWDOWN": "ArrowDown", "ARROWLEFT": "ArrowLeft",
        "ARROWRIGHT": "ArrowRight", "UP": "ArrowUp", "DOWN": "ArrowDown",
        "LEFT": "ArrowLeft", "RIGHT": "ArrowRight", "TAB": "Tab", "ENTER": "Enter",
        "ESC": "Escape", "ESCAPE": "Escape", "BACKSPACE": "Backspace", "DELETE": "Delete",
        "SPACE": "Space", "HOME": "Home", "END": "End", "PAGEDOWN": "PageDown", "PAGEUP": "PageUp",
    }

    def __init__(self, context: BrowserContext, origin: str, cancelled, *, max_actions=16, policy=None):
        self.context = context
        self.routes_in_flight = 0
        self.closing = False
        self.origin = origin
        self.policy = policy
        self.policy_error = None
        self.route_error = None
        self.write_destination = None
        self.cancelled = cancelled
        self.remaining = max_actions
        self.actions = []
        self.capture_count = 0
        self.screenshot_stage = None
        self.capture_state = None
        self.on_screenshot = None
        context.set_default_timeout(3000)
        context.set_default_navigation_timeout(5000)
        context.route("**/*", self._route)
        context.route_web_socket("**/*", lambda socket: socket.close())
        self.page: Page = context.new_page()
        self.popup_opened = False
        self.page.on("popup", self._close_popup)
        self.page.goto(origin + "/", wait_until="domcontentloaded")

    def _close_popup(self, popup):
        self.popup_opened = True
        popup.close()

    def allows(self, url):
        parts = urlsplit(url)
        return (f"{parts.scheme}://{parts.netloc}" == self.origin
                and not parts.query
                and (parts.path in {"/", "/login/", "/portal/login/"} or parts.path.startswith("/static/")
                     or (self.policy is not None and self.policy.allows_page(parts.path))))

    def _route(self, route):
        self.routes_in_flight += 1
        try:
            if self.closing:
                route.abort("blockedbyclient")
            else:
                self._handle_request(route)
        finally:
            self.routes_in_flight -= 1

    def _drain_routes(self):
        deadline = time.monotonic() + 3.5
        while self.routes_in_flight:
            if time.monotonic() >= deadline:
                raise RuntimeError("Browser route handlers did not finish before the deadline.")
            self.page.wait_for_timeout(20)

    def close(self):
        self.closing = True
        try:
            self._drain_routes()
        finally:
            self.context.close()

    def _handle_request(self, route):
        request = route.request
        if request.method in {"GET", "HEAD"} and self.allows(request.url):
            # Fetch without following redirects and give Chromium the response.
            # A redirected request then goes through this policy independently.
            self._fetch_and_fulfill(route)
        elif (self.policy is not None and request.method == "POST"
              and urlsplit(request.url).netloc == urlsplit(self.origin).netloc
              and urlsplit(request.url).scheme == "http" and not urlsplit(request.url).query
              and self.policy.allow_post(request.url, request.post_data)):
            self._fetch_and_fulfill(route, observe_write=True)
        else:
            if self.policy is not None and request.method == "POST":
                self.policy_error = RuntimeError("A write outside the approved scenario was blocked.")
            route.abort("blockedbyclient")

    def _fetch_and_fulfill(self, route, *, observe_write=False):
        try:
            response = route.fetch(max_redirects=0, max_retries=0, timeout=3000)
        except Error as error:
            # Report the original failure on the next driver boundary.
            if self.route_error is None:
                self.route_error = error
            route.abort("failed")
            return
        try:
            if observe_write:
                try:
                    self.policy.observe_post(response.status)
                    location = response.headers.get("location")
                    if response.status == 302 and location:
                        self.write_destination = urljoin(route.request.url, location)
                except RuntimeError as error:
                    self.policy_error = error
            route.fulfill(response=response)
        finally:
            response.dispose()

    def _check(self):
        if self.policy_error:
            raise self.policy_error
        if self.route_error:
            raise self.route_error
        if self.page.is_closed():
            raise RuntimeError("The browser page closed unexpectedly.")
        if self.cancelled():
            raise RuntimeError("Browser operation cancelled.")
        if self.popup_opened or not self.allows(self.page.url):
            raise RuntimeError("Browser left the allowed page context.")

    def before_action(self, action):
        self._check()
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        self.actions.append(action.type)
        return True

    def _point(self, point):
        if not (0 <= point.x < self.WIDTH and 0 <= point.y < self.HEIGHT):
            raise ValueError("Coordinates outside the browser viewport.")
        return point.x, point.y

    @staticmethod
    def _reject_modifiers(action):
        if getattr(action, "keys", None):
            raise ValueError("Pointer modifier keys are outside the smoke-test policy.")

    def click(self, action):
        self._reject_modifiers(action)
        if action.button != "left":
            raise ValueError("Only the primary mouse button is enabled.")
        x, y = self._point(action)
        previous_path = urlsplit(self.page.url).path
        destination = None
        if self.policy is not None or previous_path == "/":
            destination = self.page.evaluate(
                """([x, y]) => {
                    const link = document.elementFromPoint(x, y)?.closest('a[href]');
                    return link && (!link.target || link.target === '_self') ? link.href : null;
                }""",
                [x, y],
            )
        self.page.mouse.click(x, y)
        portal_entry = destination in {self.origin + "/login/", self.origin + "/portal/login/"}
        scenario_link = (self.policy is not None and destination and self.allows(destination)
                         and urlsplit(destination).path != previous_path)
        if portal_entry or scenario_link:
            # A generic load-state wait can still observe the outgoing document.
            self.page.wait_for_url(destination, wait_until="domcontentloaded", timeout=5000)

    def double_click(self, action):
        self._reject_modifiers(action)
        self.page.mouse.dblclick(*self._point(action))

    def move(self, action):
        self._reject_modifiers(action)
        self.page.mouse.move(*self._point(action))

    def drag(self, action):
        self._reject_modifiers(action)
        if not 2 <= len(action.path) <= 32:
            raise ValueError("Drag path must contain 2–32 coordinates.")
        start, *points = [self._point(point) for point in action.path]
        self.page.mouse.move(*start)
        self.page.mouse.down()
        try:
            for point in points:
                self._check()
                self.page.mouse.move(*point)
        finally:
            self.page.mouse.up()

    def scroll(self, action):
        self._reject_modifiers(action)
        if max(abs(action.scroll_x), abs(action.scroll_y)) > 1600:
            raise ValueError("Scroll exceeds the per-action limit.")
        self.page.mouse.move(*self._point(action))
        self.page.mouse.wheel(action.scroll_x, action.scroll_y)

    def keypress(self, action):
        if [key.upper() for key in action.keys] == ["SHIFT", "TAB"]:
            self.page.keyboard.press("Shift+Tab")
        elif len(action.keys) == 1 and (key := self.KEY_ALIASES.get(action.keys[0].upper())):
            self.page.keyboard.press(key)
        elif self.policy is not None and len(action.keys) == 1 and len(action.keys[0]) == 1 and action.keys[0] in "0123456789":
            self.page.keyboard.press(action.keys[0])
        else:
            if len(action.keys) == 1:
                signature = "keypress_unrecognized_single_key"
            elif action.keys:
                signature = "keypress_disallowed_combination"
            else:
                signature = "keypress_empty"
            raise KeypressRejected(signature)

    def type(self, action):
        if len(action.text) > 256 or not action.text.isprintable():
            raise ValueError("Typing requires printable text up to 256 characters.")
        if self.policy is not None:
            password_field = self.page.locator('input[type="password"]:focus')
            if action.text == "QA_PASSWORD" and self.page.url == self.origin + "/login/" and password_field.count():
                password_field.fill(self.policy.fixture["password"])
                return
            if password_field.count() or action.text == "QA_PASSWORD":
                raise ValueError("Password input is restricted to the designated local credential field.")
        if self.policy is not None:
            date_inputs = {
                "/app/patients/new/": ("dob", "1990-01-15"),
                "/app/appointments/new/": ("start_at", self.policy.fixture.get("start")),
            }
            expected = date_inputs.get(urlsplit(self.page.url).path)
            if expected and action.text == expected[1]:
                field = self.page.locator(f'input[name="{expected[0]}"]:focus')
                if not field.count():
                    raise ValueError("Focus the designated date or time field before entering the fixture value.")
                field.fill(action.text)
                return
        self.page.keyboard.insert_text(action.text)

    def wait(self, action):
        self.page.wait_for_timeout(250)

    def _capture_path(self, url):
        path = urlsplit(url).path
        if self.allows(url) and not path.startswith("/static/"):
            return path
        return None

    def _wait_for_write_destination(self):
        destination = self.write_destination
        if destination:
            self.screenshot_stage = "write_navigation"
            if not self.allows(destination):
                raise RuntimeError("An approved write redirected outside the scenario.")
            self.page.wait_for_url(destination, wait_until="domcontentloaded", timeout=5000)
            if self.write_destination == destination:
                self.write_destination = None

    def _capture_png(self):
        for attempt in range(3):
            self._check()
            self.screenshot_stage = "route_drain"
            self._drain_routes()
            self._check()
            self._wait_for_write_destination()
            self.screenshot_stage = "document_load"
            self.page.wait_for_load_state("load", timeout=5000)
            self._check()
            self.screenshot_stage = "playwright_capture"
            self.capture_state = {
                "path": self._capture_path(self.page.url),
                "attempt": attempt + 1,
                "load_wait_completed": True,
                "routes_in_flight": self.routes_in_flight,
                "page_closed": self.page.is_closed(),
            }
            masked = [self.page.locator('input[type="password"]')] if self.policy is not None else []
            try:
                png = self.page.screenshot(timeout=3000, animations="disabled", scale="css", mask=masked)
            except Error as error:
                if attempt == 2 or str(error).partition("\n")[0] not in {
                    CAPTURE_DOCUMENT_REPLACED, CAPTURE_NAVIGATION_PENDING,
                }:
                    raise
                # Yield to Chromium so the incoming document can commit before the next capture.
                self.page.wait_for_timeout(100)
                continue
            if not self.write_destination:
                return png
            # A write response arrived during capture. Discard the possibly stale image.
            self._wait_for_write_destination()
        raise RuntimeError("Navigation did not settle within the screenshot attempt limit.")

    def screenshot(self):
        self.capture_state = None
        self.screenshot_stage = "driver_state"
        self._check()
        png = self._capture_png()
        self.screenshot_stage = "driver_state"
        self._check()
        self.screenshot_stage = "png_encoding"
        screenshot = {"type": "computer_screenshot",
                      "image_url": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}
        self.capture_count += 1
        if self.on_screenshot:
            self.screenshot_stage = "evidence_write"
            self.on_screenshot(screenshot)
        self.screenshot_stage = "sdk_output_validation"
        return screenshot
