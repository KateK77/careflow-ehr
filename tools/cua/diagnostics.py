"""Content-free diagnostics for the native ComputerToolset smoke."""
from openai import APIError
from playwright.sync_api import Error as PlaywrightError


CAPTURE_DOCUMENT_REPLACED = "Page.screenshot: Execution context was destroyed, most likely because of a navigation"

CAPTURE_NAVIGATION_PENDING = "Page.screenshot: Frame is currently attempting a navigation"


class KeypressRejected(ValueError):
    def __init__(self, signature):
        super().__init__("Keyboard shortcut is outside the smoke-test policy.")
        self.signature = signature


def safe_exception_chain(error):
    """Keep exception types and recognized browser signatures, omitting raw messages."""
    chain, seen = [], set()
    while error is not None and id(error) not in seen and len(chain) < 6:
        seen.add(id(error))
        entry = {"class": type(error).__name__}
        if isinstance(error, KeypressRejected):
            entry["signature"] = error.signature
        if isinstance(error, PlaywrightError):
            headline = str(error).partition("\n")[0]
            if headline == CAPTURE_DOCUMENT_REPLACED:
                entry["signature"] = "capture_document_replaced"
            elif headline == CAPTURE_NAVIGATION_PENDING:
                entry["signature"] = "capture_navigation_pending"
            elif "Route.fetch: Request context disposed" in headline:
                entry["signature"] = "route_request_context_disposed"
            elif headline.startswith("Page.screenshot: Timeout "):
                entry["signature"] = "capture_timeout"
            elif headline.startswith("Page.screenshot: Target page, context or browser has been closed"):
                entry["signature"] = "capture_target_closed"
            elif headline.startswith("Page.screenshot: Protocol error"):
                entry["signature"] = "capture_protocol_error"
        chain.append(entry)
        error = error.__cause__ or (None if error.__suppress_context__ else error.__context__)
    return chain


API_CODES = {
    "model_not_found", "unsupported_model", "model_not_supported", "unsupported_tool",
    "tool_not_supported", "unsupported_value", "invalid_value", "invalid_request_error",
    "invalid_api_key", "insufficient_quota", "rate_limit_exceeded", "context_length_exceeded",
    "server_error", "invalid_prompt", "content_filter",
}
SDK_FAILURES = {
    "Response did not complete": "response_incomplete",
    "Computer call did not complete": "computer_call_incomplete",
    "Computer call requires exactly one of action or actions": "invalid_computer_call_shape",
    "Computer call has no actions": "empty_computer_call",
    "Invalid computer action": "invalid_computer_action",
    "Response requires native reasoning content before replay": "invalid_native_reasoning",
    "Response requires native assistant content before replay": "invalid_native_assistant_content",
    "Driver must return a computer_screenshot with image_url or file_id": "invalid_driver_screenshot",
    "Computer run reached max_steps before completion": "step_limit",
    "Response has no final message or computer call": "missing_final_message_or_call",
    "Response requires a tool this helper does not handle": "unsupported_response_tool",
    "Computer safety checks require explicit approval": "safety_check_refused",
    "Computer action was not approved": "action_refused",
    "Computer run was cancelled": "cancelled",
}
ACTION_MEMBERS = {"click", "double_click", "drag", "keypress", "move", "scroll", "type", "wait", "screenshot"}
FAILURE_REASONS = {"refused", "cancelled", "driver_failed", "policy_failed", "invalid_output"}


class Diagnostics:
    def __init__(self):
        self.stage = "configuration"
        self.attempts = 0
        self.responses = 0
        self.status = None
        self.event = None
        self.actions = []
        self.completed_actions = []
        self.checkpoints = []
        self.checks = {}
        self.usage = []
        self.evidence_ready = False
        self.screenshot_stage = None
        self.capture_state = None
        self.exception_chain = []

    def capture_usage(self, response):
        if response.status_code != 200:
            return
        response.read()
        try:
            usage = response.json().get("usage") or {}
            counts = tuple(usage.get(field) for field in ("input_tokens", "output_tokens"))
        except (ValueError, AttributeError):
            return
        if all(type(count) is int and count >= 0 for count in counts):
            self.usage.append(counts)

    def usage_summary(self, priced):
        input_tokens = sum(counts[0] for counts in self.usage)
        output_tokens = sum(counts[1] for counts in self.usage)
        return {
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "responses_with_usage": len(self.usage),
            "complete": len(self.usage) == self.attempts,
            "estimated_token_cost_usd": (
                round((input_tokens * 2.50 + output_tokens * 15.00) / 1_000_000, 6)
                if priced and self.usage else None
            ),
        }

    def request_started(self, request):
        self.stage = "responses_request"
        self.attempts += 1
        self.status = None
        self.event = None

    def response_received(self, response):
        self.stage = "responses_validation"
        self.responses += 1
        self.status = response.status_code

    def tool_event(self, event):
        stage, reason, member = event["stage"], event["reason"], event["member"]
        if stage == "action" and reason == "completed" and member in ACTION_MEMBERS:
            self.completed_actions.append(member)
        if stage in {"approval", "action"} and reason in FAILURE_REASONS:
            if stage == "approval":
                self.stage = "computer_approval"
            else:
                self.stage = "computer_screenshot" if member == "screenshot" else "computer_action"
            self.event = (reason, member if member in ACTION_MEMBERS else "none")

    def failure(self, error):
        self.exception_chain = safe_exception_chain(error)
        status = getattr(error, "status_code", self.status)
        response = getattr(error, "response", None)
        detail = getattr(getattr(response, "incomplete_details", None), "reason", None)
        code = getattr(error, "code", None) or getattr(getattr(response, "error", None), "code", None)
        safe_code = code if isinstance(code, str) and code in API_CODES else ("unrecognized" if code else "none")
        # Only exact, fixed SDK strings are classified. Never print exception messages.
        reason = SDK_FAILURES.get(error.args[0], "unclassified") if (
            type(error).__name__ == "ComputerUseError" and error.args and isinstance(error.args[0], str)
        ) else "unclassified"
        if detail in ("max_output_tokens", "content_filter"):
            reason = detail
        compatibility = "no signal"
        if safe_code in {"model_not_found", "unsupported_model", "model_not_supported"}:
            compatibility = "check model name, project access and native computer support"
        elif safe_code in {"unsupported_tool", "tool_not_supported"} or reason == "unsupported_response_tool":
            compatibility = "check model support for the native computer tool"
        elif isinstance(error, APIError) and status in (400, 404, 422):
            param = error.param
            if isinstance(param, str) and (param == "model" or param == "tools" or param.startswith("tools[")):
                compatibility = "API rejected the model or tool configuration"
        if isinstance(error, APIError) and self.stage != "request_budget":
            self.stage = "responses_request" if not self.status else "responses_api"
        if self.status is not None:
            sent = "confirmed by HTTP response"
        elif self.attempts:
            sent = "attempted; delivery unconfirmed"
        else:
            sent = "no"
        event_reason, member = self.event or ("none", "none")
        return (
            f"Smoke failed ({type(error).__name__}). Stage: {self.stage}. "
            f"HTTP status: {status if type(status) is int else 'none'}. API code: {safe_code}. "
            f"Reason: {reason}. Tool event: {event_reason}/{member}. Compatibility: {compatibility}. "
            f"Request sent: {sent} ({self.attempts} attempted, {self.responses} HTTP responses)."
        )
