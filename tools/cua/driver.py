"""Browser-only implementation of the OpenAI native computer driver contract."""
import base64
import time
from urllib.parse import urlsplit

from openai import ComputerDriver
from playwright.sync_api import BrowserContext, Page


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
        self.origin = origin
        self.policy = policy
        self.policy_error = None
        self.cancelled = cancelled
        self.remaining = max_actions
        self.actions = []
        self.capture_count = 0
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
        request = route.request
        if request.method in {"GET", "HEAD"} and self.allows(request.url):
            # Fetch without following redirects and give Chromium the response.
            # A redirected request then goes through this policy independently.
            route.fulfill(response=route.fetch(max_redirects=0, max_retries=0, timeout=3000))
        elif (self.policy is not None and request.method == "POST"
              and urlsplit(request.url).netloc == urlsplit(self.origin).netloc
              and urlsplit(request.url).scheme == "http" and not urlsplit(request.url).query
              and self.policy.allow_post(request.url, request.post_data)):
            response = route.fetch(max_redirects=0, max_retries=0, timeout=3000)
            try:
                self.policy.observe_post(response.status)
            except RuntimeError as error:
                self.policy_error = error
            route.fulfill(response=response)
        else:
            if self.policy is not None and request.method == "POST":
                self.policy_error = RuntimeError("A write outside the approved scenario was blocked.")
            route.abort("blockedbyclient")

    def _check(self):
        if self.policy_error:
            raise self.policy_error
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
        self.page.mouse.click(*self._point(action))

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
            raise ValueError("Keyboard shortcut is outside the smoke-test policy.")

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
        self.page.keyboard.insert_text(action.text)

    def wait(self, action):
        self.page.wait_for_timeout(250)

    def screenshot(self):
        self._check()
        masked = [self.page.locator('input[type="password"]')] if self.policy is not None else []
        png = self.page.screenshot(timeout=3000, animations="disabled", scale="css", mask=masked)
        self._check()
        screenshot = {"type": "computer_screenshot",
                      "image_url": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}
        self.capture_count += 1
        if self.on_screenshot:
            self.on_screenshot(screenshot)
        return screenshot
